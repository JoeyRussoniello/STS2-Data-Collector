mod discovery;
mod record;
mod retry;
mod state;
mod upload;
mod watcher;

use std::io;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc;
use std::sync::Arc;
use std::time::Duration;

use crate::discovery::{discover_existing_run_records, discover_save_dirs, get_sts2_base_dir};
use crate::record::{parse_run_path, RunFileRecord};
use crate::retry::RetryQueue;
use crate::state::ClientState;
use crate::upload::{UploadResult, Uploader};
use crate::watcher::{start_watchers, RunEvent};

const VERSION: &str = env!("CARGO_PKG_VERSION");
const FRONTEND_URL_BASE: &'static str = "https://sts-2-data-collector.vercel.app/";

fn main() {
    if let Err(err) = run() {
        eprintln!("Fatal: {err}");
        std::process::exit(1);
    }
}

fn print_banner() {
    println!("╔══════════════════════════════════════════╗");
    println!("║     STS2 Data Collector  v{VERSION:<13}  ║");
    println!("║   Collecting Slay the Spire 2 run data   ║");
    println!("╚══════════════════════════════════════════╝");
    println!();
}

fn run() -> io::Result<()> {
    print_banner();

    let sts_base = get_sts2_base_dir()?;
    println!("Save directory: {}", sts_base.display());

    let mut state = ClientState::load(&sts_base)?;
    let uploader = Uploader::new();
    let mut retry_queue = RetryQueue::new();

    // --- startup scan ---
    let existing = discover_existing_run_records()?;
    let new_records: Vec<&RunFileRecord> =
        existing.iter().filter(|r| !state.contains(&r.id)).collect();

    if new_records.is_empty() {
        println!("No new run files to process.");
    } else {
        println!("Found {} new run file(s) to upload.", new_records.len());
        for record in &new_records {
            match uploader.upload_record(record) {
                UploadResult::Success => {
                    state.mark_uploaded(record.id.clone())?;
                }
                UploadResult::Retryable(msg) => {
                    eprintln!("  Retryable failure for {}: {msg}", record.id);
                    retry_queue.push((*record).clone());
                }
                UploadResult::Permanent(msg) => {
                    eprintln!("  Permanent failure for {}: {msg}", record.id);
                }
            }
        }
    }

    // --- discover watch targets ---
    let save_dirs = discover_save_dirs()?;
    println!("Watching {} history dir(s) for new runs.", save_dirs.len());

    // --- start filesystem watchers ---
    let (tx, rx) = mpsc::channel();
    let _watchers = start_watchers(&save_dirs, tx)?;

    // --- start stdin quit listener ---
    let quit_flag = Arc::new(AtomicBool::new(false));
    spawn_quit_listener(Arc::clone(&quit_flag));

    println!();
    println!("Listening for new runs. Press 'q' + Enter to quit.");
    if !retry_queue.is_empty() {
        println!("  ({} upload(s) queued for retry)", retry_queue.len());
    }

    // Print personal dashboard links for discovered players
    let mut steam_ids: Vec<&str> = existing.iter().map(|r| r.steam_id.as_str()).collect();
    steam_ids.sort();
    steam_ids.dedup();
    if !steam_ids.is_empty() {
        println!();
        println!("View your stats at:");
        for sid in &steam_ids {
            println!("  -> {FRONTEND_URL_BASE}/#overview/{sid}");
        }
    }

    println!();

    // --- event loop: process events + retry queue ---
    run_event_loop(rx, &mut state, &uploader, &mut retry_queue, &quit_flag)
}

/// Spawn a thread that reads stdin and sets the quit flag when the user types "q".
fn spawn_quit_listener(quit_flag: Arc<AtomicBool>) {
    std::thread::spawn(move || {
        let stdin = std::io::stdin();
        let mut line = String::new();
        loop {
            line.clear();
            if stdin.read_line(&mut line).is_err() {
                break;
            }
            let trimmed = line.trim().to_lowercase();
            if trimmed == "q" || trimmed == "quit" {
                quit_flag.store(true, Ordering::SeqCst);
                break;
            }
        }
    });
}

/// Process incoming `.run` file events and drain the retry queue.
fn run_event_loop(
    rx: mpsc::Receiver<RunEvent>,
    state: &mut ClientState,
    uploader: &Uploader,
    retry_queue: &mut RetryQueue,
    quit_flag: &AtomicBool,
) -> io::Result<()> {
    loop {
        if quit_flag.load(Ordering::SeqCst) {
            println!("Shutting down. Goodbye!");
            return Ok(());
        }

        // Check for new watcher events (non-blocking with timeout)
        match rx.recv_timeout(Duration::from_secs(1)) {
            Ok(RunEvent::NewRunFile(path)) => {
                let (steam_id, profile) = match parse_run_path(&path) {
                    Ok(ids) => ids,
                    Err(err) => {
                        eprintln!("Skipping {}: {err}", path.display());
                        continue;
                    }
                };

                let record = RunFileRecord::from_file(&steam_id, &profile, &path)?;

                if state.contains(&record.id) {
                    continue;
                }

                println!("New run detected: {}", record.id);
                match uploader.upload_record(&record) {
                    UploadResult::Success => {
                        state.mark_uploaded(record.id)?;
                    }
                    UploadResult::Retryable(msg) => {
                        eprintln!("  Retryable failure for {}: {msg}", record.id);
                        retry_queue.push(record);
                    }
                    UploadResult::Permanent(msg) => {
                        eprintln!("  Permanent failure for {}: {msg}", record.id);
                    }
                }
            }
            Err(mpsc::RecvTimeoutError::Timeout) => {}
            Err(mpsc::RecvTimeoutError::Disconnected) => {
                eprintln!("All watchers stopped unexpectedly.");
                return Ok(());
            }
        }

        // Drain ready retries
        let ready = retry_queue.drain_ready();
        for entry in ready {
            println!("  Retrying upload: {} (attempt {})", entry.record.id, entry.attempts + 1);
            match uploader.upload_record(&entry.record) {
                UploadResult::Success => {
                    state.mark_uploaded(entry.record.id.clone())?;
                }
                UploadResult::Retryable(msg) => {
                    if !retry_queue.repush(entry.clone()) {
                        eprintln!(
                            "  Giving up on {} after {} attempts: {msg}",
                            entry.record.id, entry.attempts
                        );
                    }
                }
                UploadResult::Permanent(msg) => {
                    eprintln!("  Permanent failure for {}: {msg}", entry.record.id);
                }
            }
        }
    }
}

#[cfg(test)]
mod tests;