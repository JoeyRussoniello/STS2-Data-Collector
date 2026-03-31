use std::io;
use std::path::{Path, PathBuf};
use std::sync::mpsc::Sender;
use std::time::Duration;

use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};

/// A filesystem event relevant to the run-file pipeline.
#[derive(Debug)]
pub enum RunEvent {
    /// A new or modified `.run` file was detected at this path.
    NewRunFile(PathBuf),
}

/// Start a `notify` watcher on each `saves/history` directory.
///
/// Every time a `.run` file is created or modified, a `RunEvent::NewRunFile`
/// is sent through `tx`.  The returned watchers must be kept alive for the
/// duration of the program — dropping them stops monitoring.
pub fn start_watchers(
    save_dirs: &[PathBuf],
    tx: Sender<RunEvent>,
) -> io::Result<Vec<RecommendedWatcher>> {
    let mut watchers = Vec::with_capacity(save_dirs.len());

    for dir in save_dirs {
        let watcher = create_watcher(dir, tx.clone())?;
        watchers.push(watcher);
    }

    Ok(watchers)
}

fn is_run_file(path: &Path) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.eq_ignore_ascii_case("run"))
        .unwrap_or(false)
}

fn create_watcher(dir: &Path, tx: Sender<RunEvent>) -> io::Result<RecommendedWatcher> {
    let mut watcher = RecommendedWatcher::new(
        move |result: Result<Event, notify::Error>| {
            let event = match result {
                Ok(e) => e,
                Err(err) => {
                    eprintln!("Watcher error: {err}");
                    return;
                }
            };

            // We care about newly created files and files that finished writing.
            match event.kind {
                EventKind::Create(_) | EventKind::Modify(_) => {}
                _ => return,
            }

            for path in event.paths {
                if path.is_file() && is_run_file(&path) {
                    if tx.send(RunEvent::NewRunFile(path)).is_err() {
                        // Receiver dropped — nothing we can do.
                        return;
                    }
                }
            }
        },
        Config::default().with_poll_interval(Duration::from_secs(2)),
    )
    .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;

    watcher
        .watch(dir, RecursiveMode::NonRecursive)
        .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;

    Ok(watcher)
}
