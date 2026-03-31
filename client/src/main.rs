mod discovery;
mod record;
mod state;
mod upload;
mod watcher;

use std::io;

use crate::discovery::{discover_existing_run_records, discover_save_dirs, get_sts2_base_dir};
use crate::record::RunFileRecord;
use crate::state::ClientState;

fn main() {
    if let Err(err) = run() {
        eprintln!("Fatal: {err}");
        std::process::exit(1);
    }
}

fn run() -> io::Result<()> {
    let sts_base = get_sts2_base_dir()?;
    let mut state = ClientState::load(&sts_base)?;

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
            // TODO: upload_record(record)?;
            state.mark_uploaded(record.id.clone())?;
        }
    }

    // --- discover watch targets ---
    let save_dirs = discover_save_dirs()?;
    println!("Watching {} history dir(s) for new runs…", save_dirs.len());

    // TODO: start_watchers(&save_dirs, tx)?;
    // TODO: run_event_loop(rx, &mut state)?;

    Ok(())
}

#[cfg(test)]
mod tests;