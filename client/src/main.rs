use std::collections::HashSet;
use std::env;
use std::fs::{self, File};
use std::io::{self, Read};
use std::path::{Path, PathBuf};

use std::hash::{DefaultHasher, Hash, Hasher};

#[derive(Debug, Clone)]
struct RunFileRecord {
    id: String, 
    profile: String,
    path: PathBuf,
    file_name: String,
    ///! Important. Steam ID MUST BE HASHED ON THE SERVER SIDE
    steam_id: String,
    size_bytes: u64,
}

impl RunFileRecord{
    fn from_file(steam_id: &str, profile: &str, run_file: &PathBuf) -> io::Result<Self>{
        let size_bytes = run_file.metadata()?.len();
        let run_id = file_name_string(run_file)?;
        let id = format!("{}{}{}",steam_id,profile,run_id);
        return Ok(Self{
            id,
            profile: profile.to_string(),
            path: run_file.clone(),
            file_name: run_id,
            steam_id: steam_id.to_string(),
            size_bytes
        })
    }
}

fn main() {
    match discover_and_hash_runs() {
        Ok(records) => {
            if records.is_empty() {
                println!("No run files found.");
                return;
            }

            println!("Found {} run file(s):", records.len());
            for record in records {
                println!("{:?}", record);
            }
        }
        Err(err) => {
            eprintln!("Error discovering run files: {err}");
            std::process::exit(1);
        }
    }
}


fn discover_and_hash_runs() -> io::Result<Vec<RunFileRecord>>{
    let sts_base = get_sts2_base_dir()?;
    let steam_dir = sts_base.join("steam");

    if !steam_dir.exists(){
        return Ok(Vec::new());
    }

    let mut records: Vec<RunFileRecord> = Vec::new();
    let steam_ids = list_child_dirs(&steam_dir)?;

    // Likely will only be one
    for steam_id_dir in steam_ids{
        let steam_id = file_name_string(&steam_id_dir)?;

        let profile_dirs = get_profile_dirs(&steam_id_dir)?;
        for profile in profile_dirs{
            let profile_name = file_name_string(&profile)?;
            let run_files = get_run_files_for_profile(&profile)?;
            let profile_records = convert_run_files_to_records(&run_files, &steam_id, &profile_name)?;
            records.extend(profile_records);
        }
    }
    Ok(records)     
}

fn get_sts2_base_dir() -> io::Result<PathBuf> {
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

fn list_child_dirs(root: &Path) -> io::Result<Vec<PathBuf>>{
    let mut dirs: Vec<PathBuf> = fs::read_dir(root)?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        .collect();
    dirs.sort();
    Ok(dirs)
}

fn is_profile_dir(dir: &Path) -> io::Result<bool>{
    let is_profile = file_name_string(dir)?.to_lowercase().starts_with("profile");
    Ok(is_profile)
}
fn get_profile_dirs(root: &Path) -> io::Result<Vec<PathBuf>>{
    let mut profiles: Vec<PathBuf> = Vec::new();

    for dir in list_child_dirs(root)?{
        let is_profile = is_profile_dir(&dir)?;
        if is_profile{
            profiles.push(dir)
        }
    }

    return Ok(profiles)
}
fn file_name_string(path: &Path) -> io::Result<String> {
    path.file_name()
        .and_then(|name| name.to_str())
        .map(|s| s.to_string())
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, format!("Invalid UTF-8 path: {}", path.display())))
}

fn get_run_files_for_profile(profile: &Path) -> io::Result<Vec<PathBuf>>{
    let run_dir = profile.join("saves").join("history");
    if (!run_dir.exists()){
        return Ok(Vec::new())
    }

    let mut run_files = Vec::new();
    let mut seen = HashSet::new();

    for file in fs::read_dir(profile)?{

        let path = file?.path();
        if !path.is_file() {continue}
        let is_run = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| ext.eq_ignore_ascii_case("run"))
            .unwrap_or(false);
        
        if !is_run{continue}

        if (seen.insert(path.clone())){
            run_files.push(path);
        }

    }
    
    Ok(run_files)
}

fn convert_run_files_to_records(run_files: &Vec<PathBuf>, steam_id: &str, profile_name: &str) -> io::Result<Vec<RunFileRecord>>{
    let mut records = Vec::new();
    for file in run_files{
        let record = RunFileRecord::from_file(steam_id, profile_name, file)?;
        records.push(record);
    } 
    Ok(records)
}