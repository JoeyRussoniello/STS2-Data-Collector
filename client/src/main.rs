mod discovery;
mod record;
mod state;
mod upload;
mod watcher;

use std::io;
use std::sync::mpsc;

use crate::discovery::{discover_existing_run_records, discover_save_dirs, get_sts2_base_dir};
use crate::record::{parse_run_path, RunFileRecord};
use crate::state::ClientState;
use crate::upload::Uploader;
use crate::watcher::{start_watchers, RunEvent};

fn main() {
    if let Err(err) = run() {
        eprintln!("Fatal: {err}");
        std::process::exit(1);
    }
}

fn run() -> io::Result<()> {
    let sts_base = get_sts2_base_dir()?;
    let mut state = ClientState::load(&sts_base)?;
    let uploader = Uploader::new();

    // --- startup scan ---
    let existing = discover_existing_run_records()?;
    let new_records: Vec<&RunFileRecord> =
        existing.iter().filter(|r| !state.contains(&r.id)).collect();

    if new_records.is_empty() {
        println!("No new run files to process.");
    } else {
        println!("Found {} new run file(s):", new_records.len());
        for record in &new_records {
            println!("  {}", record.id);
            if let Err(e) = uploader.upload_record(record) {
                eprintln!("  Upload failed for {}: {e}", record.id);
                continue;
            }
            state.mark_uploaded(record.id.clone())?;
        }
    }

    // --- discover watch targets ---
    let save_dirs = discover_save_dirs()?;
    println!("Watching {} history dir(s) for new runs…", save_dirs.len());

    // --- start filesystem watchers ---
    let (tx, rx) = mpsc::channel();
    let _watchers = start_watchers(&save_dirs, tx)?;

    // --- event loop: process new .run files as they appear ---
    run_event_loop(rx, &mut state, &uploader)
}

/// Block forever, processing incoming `.run` file events.
fn run_event_loop(
    rx: mpsc::Receiver<RunEvent>,
    state: &mut ClientState,
    uploader: &Uploader,
) -> io::Result<()> {
    for event in rx {
        match event {
            RunEvent::NewRunFile(path) => {
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
                if let Err(e) = uploader.upload_record(&record) {
                    eprintln!("  Upload failed for {}: {e}", record.id);
                    continue;
                }
                state.mark_uploaded(record.id)?;
            }
        }
    }

    // Channel closed, all watchers dropped.
    Ok(())
}

#[cfg(test)]
mod tests;