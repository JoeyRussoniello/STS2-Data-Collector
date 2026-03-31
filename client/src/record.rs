use std::io;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone)]
pub struct RunFileRecord {
    pub id: String,
    pub profile: String,
    pub path: PathBuf,
    pub file_name: String,
    ///! Important. Steam ID MUST BE HASHED ON THE SERVER SIDE
    pub steam_id: String,
    pub size_bytes: u64,
}

impl RunFileRecord {
    pub fn from_file(steam_id: &str, profile: &str, run_file: &PathBuf) -> io::Result<Self> {
        let size_bytes = run_file.metadata()?.len();
        let run_id = file_name_string(run_file)?;
        let id = format!("{profile}:{run_id}");
        Ok(Self {
            id,
            profile: profile.to_string(),
            path: run_file.clone(),
            file_name: run_id,
            steam_id: steam_id.to_string(),
            size_bytes,
        })
    }
}

/// Extract the final component of a path as a String, stripping the `.run` extension.
pub fn file_name_string(path: &Path) -> io::Result<String> {
    path.file_stem()
        .and_then(|name| name.to_str())
        .map(|s| s.to_string())
        .ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::InvalidData,
                format!("Invalid UTF-8 path: {}", path.display()),
            )
        })
}

/// Given a path like `.../steam/<steam_id>/<profile>/saves/history/foo.run`,
/// extract `(steam_id, profile)` by walking ancestors.
pub fn parse_run_path(run_file: &Path) -> io::Result<(String, String)> {
    // Expected structure: .../steam/<steam_id>/<profile>/saves/history/<file>.run
    // Walk up: history -> saves -> profile -> steam_id
    let history = run_file
        .parent()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "run file has no parent"))?;
    let saves = history
        .parent()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "history has no parent"))?;
    let profile_dir = saves
        .parent()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "saves has no parent"))?;
    let steam_id_dir = profile_dir
        .parent()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "profile has no parent"))?;

    let steam_id = file_name_string(steam_id_dir)?;
    let profile = file_name_string(profile_dir)?;
    Ok((steam_id, profile))
}
