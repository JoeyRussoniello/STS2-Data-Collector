use std::collections::HashSet;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

const STATE_FILE: &str = "uploaded_runs.txt";

pub struct ClientState {
    uploaded_run_ids: HashSet<String>,
    state_path: PathBuf,
}

impl ClientState {
    /// Load state from disk, or start empty if the file does not exist.
    pub fn load(state_dir: &Path) -> io::Result<Self> {
        let state_path = state_dir.join(STATE_FILE);
        let uploaded_run_ids = if state_path.exists() {
            fs::read_to_string(&state_path)?
                .lines()
                .filter(|l| !l.is_empty())
                .map(|l| l.to_string())
                .collect()
        } else {
            HashSet::new()
        };
        Ok(Self {
            uploaded_run_ids,
            state_path,
        })
    }

    pub fn contains(&self, id: &str) -> bool {
        self.uploaded_run_ids.contains(id)
    }

    pub fn mark_uploaded(&mut self, id: String) -> io::Result<()> {
        if self.uploaded_run_ids.insert(id) {
            self.persist()?;
        }
        Ok(())
    }

    fn persist(&self) -> io::Result<()> {
        if let Some(parent) = self.state_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let content: Vec<&str> = self.uploaded_run_ids.iter().map(|s| s.as_str()).collect();
        fs::write(&self.state_path, content.join("\n"))
    }
}
