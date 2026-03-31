use std::env;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use crate::record::{file_name_string, RunFileRecord};

/// Resolve the STS2 base directory (honours `STS2_BASE_DIR` env override).
pub fn get_sts2_base_dir() -> io::Result<PathBuf> {
    if let Ok(explicit) = env::var("STS2_BASE_DIR") {
        let path = PathBuf::from(explicit);
        if path.exists() {
            return Ok(path);
        }
    }

    if cfg!(target_os = "windows") {
        if let Ok(appdata) = env::var("APPDATA") {
            return Ok(PathBuf::from(appdata).join("SlayTheSpire2"));
        }
    }

    let home = env::var_os("HOME")
        .map(PathBuf::from)
        .ok_or_else(|| io::Error::new(io::ErrorKind::NotFound, "Could not resolve HOME"))?;

    Ok(home.join("AppData").join("Roaming").join("SlayTheSpire2"))
}

/// List immediate child directories of `root`, sorted.
pub fn list_child_dirs(root: &Path) -> io::Result<Vec<PathBuf>> {
    let mut dirs: Vec<PathBuf> = fs::read_dir(root)?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        .collect();
    dirs.sort();
    Ok(dirs)
}

pub fn is_profile_dir(dir: &Path) -> io::Result<bool> {
    let is_profile = file_name_string(dir)?.to_lowercase().starts_with("profile");
    Ok(is_profile)
}

pub fn get_profile_dirs(root: &Path) -> io::Result<Vec<PathBuf>> {
    let mut profiles: Vec<PathBuf> = Vec::new();
    for dir in list_child_dirs(root)? {
        if is_profile_dir(&dir)? {
            profiles.push(dir);
        }
    }
    Ok(profiles)
}

/// Collect `.run` files from `<profile>/saves/history/`.
pub fn get_run_files_for_profile(profile: &Path) -> io::Result<Vec<PathBuf>> {
    let run_dir = profile.join("saves").join("history");
    if !run_dir.exists() {
        return Ok(Vec::new());
    }

    let mut run_files = Vec::new();

    for file in fs::read_dir(run_dir)? {
        let path = file?.path();
        if !path.is_file() {
            continue;
        }
        let is_run = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| ext.eq_ignore_ascii_case("run"))
            .unwrap_or(false);
        if !is_run {
            continue;
        }
        run_files.push(path);
    }

    Ok(run_files)
}

/// Return all `saves/history` directories that the watcher should monitor.
pub fn discover_save_dirs() -> io::Result<Vec<PathBuf>> {
    let sts_base = get_sts2_base_dir()?;
    let steam_dir = sts_base.join("steam");

    if !steam_dir.exists() {
        return Ok(Vec::new());
    }

    let mut save_dirs = Vec::new();
    for steam_id_dir in list_child_dirs(&steam_dir)? {
        for profile in get_profile_dirs(&steam_id_dir)? {
            let history = profile.join("saves").join("history");
            if history.exists() {
                save_dirs.push(history);
            }
        }
    }
    Ok(save_dirs)
}

/// Walk the full STS2 tree and materialise a `RunFileRecord` for every `.run`
/// file found under any profile's `saves/history` directory.
pub fn discover_existing_run_records() -> io::Result<Vec<RunFileRecord>> {
    let sts_base = get_sts2_base_dir()?;
    let steam_dir = sts_base.join("steam");

    if !steam_dir.exists() {
        return Ok(Vec::new());
    }

    let mut records: Vec<RunFileRecord> = Vec::new();
    let steam_ids = list_child_dirs(&steam_dir)?;

    for steam_id_dir in steam_ids {
        let steam_id = file_name_string(&steam_id_dir)?;

        for profile in get_profile_dirs(&steam_id_dir)? {
            let profile_name = file_name_string(&profile)?;
            for run_file in get_run_files_for_profile(&profile)? {
                let record = RunFileRecord::from_file(&steam_id, &profile_name, &run_file)?;
                records.push(record);
            }
        }
    }
    Ok(records)
}
