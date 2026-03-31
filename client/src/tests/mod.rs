use crate::discovery::*;
use crate::record::*;
use crate::state::ClientState;
use std::collections::HashSet;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use tempfile::TempDir;

/// Helper: build the full directory tree that discover_and_hash_runs expects
/// and return the base dir (the "SlayTheSpire2" equivalent).
fn make_tree(
    base: &Path,
    steam_id: &str,
    profiles: &[&str],
    run_files_per_profile: &[&[&str]],
) {
    for (i, profile) in profiles.iter().enumerate() {
        let history = base
            .join("steam")
            .join(steam_id)
            .join(profile)
            .join("saves")
            .join("history");
        fs::create_dir_all(&history).unwrap();
        for run in run_files_per_profile[i] {
            fs::write(history.join(run), "fake-run-data").unwrap();
        }
    }
}

// ---- list_child_dirs ----

#[test]
fn list_child_dirs_returns_sorted_dirs() {
    let tmp = TempDir::new().unwrap();
    fs::create_dir(tmp.path().join("zebra")).unwrap();
    fs::create_dir(tmp.path().join("alpha")).unwrap();
    fs::write(tmp.path().join("file.txt"), "").unwrap(); // should be excluded

    let dirs = list_child_dirs(tmp.path()).unwrap();
    let names: Vec<_> = dirs.iter().map(|d| file_name_string(d).unwrap()).collect();
    assert_eq!(names, vec!["alpha", "zebra"]);
}

#[test]
fn list_child_dirs_empty_dir() {
    let tmp = TempDir::new().unwrap();
    let dirs = list_child_dirs(tmp.path()).unwrap();
    assert!(dirs.is_empty());
}

#[test]
fn list_child_dirs_nonexistent() {
    let result = list_child_dirs(Path::new("/does/not/exist"));
    assert!(result.is_err());
}

// ---- is_profile_dir ----

#[test]
fn is_profile_dir_matches_profile() {
    assert!(is_profile_dir(Path::new("/some/Profile1")).unwrap());
    assert!(is_profile_dir(Path::new("/some/profile2")).unwrap());
    assert!(is_profile_dir(Path::new("/some/PROFILE_X")).unwrap());
}

#[test]
fn is_profile_dir_rejects_non_profile() {
    assert!(!is_profile_dir(Path::new("/some/settings")).unwrap());
    assert!(!is_profile_dir(Path::new("/some/saves")).unwrap());
}

// ---- get_profile_dirs ----

#[test]
fn get_profile_dirs_filters_correctly() {
    let tmp = TempDir::new().unwrap();
    fs::create_dir(tmp.path().join("Profile1")).unwrap();
    fs::create_dir(tmp.path().join("Profile2")).unwrap();
    fs::create_dir(tmp.path().join("settings")).unwrap();

    let profiles = get_profile_dirs(tmp.path()).unwrap();
    let names: Vec<_> = profiles.iter().map(|d| file_name_string(d).unwrap()).collect();
    assert_eq!(names, vec!["Profile1", "Profile2"]);
}

#[test]
fn get_profile_dirs_none_found() {
    let tmp = TempDir::new().unwrap();
    fs::create_dir(tmp.path().join("settings")).unwrap();

    let profiles = get_profile_dirs(tmp.path()).unwrap();
    assert!(profiles.is_empty());
}

// ---- file_name_string ----

#[test]
fn file_name_string_works() {
    let s = file_name_string(Path::new("/a/b/myfile.txt")).unwrap();
    assert_eq!(s, "myfile.txt");
}

#[test]
fn file_name_string_root_fails() {
    // Root path has no file_name component
    let result = file_name_string(Path::new("/"));
    assert!(result.is_err());
}

// ---- get_run_files_for_profile ----

#[test]
fn get_run_files_finds_only_run_extension() {
    let tmp = TempDir::new().unwrap();
    let history = tmp.path().join("saves").join("history");
    fs::create_dir_all(&history).unwrap();
    fs::write(history.join("game1.run"), "data").unwrap();
    fs::write(history.join("game2.RUN"), "data").unwrap(); // case-insensitive
    fs::write(history.join("notes.txt"), "data").unwrap(); // should be excluded
    fs::write(history.join("no_ext"), "data").unwrap();    // no extension

    let files = get_run_files_for_profile(tmp.path()).unwrap();
    assert_eq!(files.len(), 2);
    let names: HashSet<_> = files.iter().map(|f| file_name_string(f).unwrap()).collect();
    assert!(names.contains("game1.run"));
    assert!(names.contains("game2.RUN"));
}

#[test]
fn get_run_files_missing_history_dir() {
    let tmp = TempDir::new().unwrap();
    // No saves/history directory at all
    let files = get_run_files_for_profile(tmp.path()).unwrap();
    assert!(files.is_empty());
}

#[test]
fn get_run_files_skips_subdirectories() {
    let tmp = TempDir::new().unwrap();
    let history = tmp.path().join("saves").join("history");
    fs::create_dir_all(&history).unwrap();
    fs::create_dir(history.join("subdir.run")).unwrap(); // dir, not file
    fs::write(history.join("real.run"), "data").unwrap();

    let files = get_run_files_for_profile(tmp.path()).unwrap();
    assert_eq!(files.len(), 1);
}

// ---- RunFileRecord::from_file ----

#[test]
fn record_from_file_captures_fields() {
    let tmp = TempDir::new().unwrap();
    let run = tmp.path().join("game1.run");
    fs::write(&run, "some run data").unwrap();

    let record = RunFileRecord::from_file("12345", "Profile1", &run).unwrap();
    assert_eq!(record.steam_id, "12345");
    assert_eq!(record.profile, "Profile1");
    assert_eq!(record.file_name, "game1.run");
    assert_eq!(record.id, "12345:Profile1:game1.run");
    assert_eq!(record.size_bytes, "some run data".len() as u64);
    assert_eq!(record.path, run);
}

#[test]
fn record_from_file_nonexistent() {
    let bad = PathBuf::from("/tmp/nonexistent_file.run");
    let result = RunFileRecord::from_file("id", "prof", &bad);
    assert!(result.is_err());
}

// ---- parse_run_path ----

#[test]
fn parse_run_path_extracts_ids() {
    let path = Path::new("/base/steam/12345/Profile1/saves/history/game.run");
    let (steam_id, profile) = parse_run_path(path).unwrap();
    assert_eq!(steam_id, "12345");
    assert_eq!(profile, "Profile1");
}

#[test]
fn parse_run_path_too_shallow() {
    let path = Path::new("game.run");
    assert!(parse_run_path(path).is_err());
}

// ---- discover_save_dirs ----

#[test]
fn discover_save_dirs_finds_history_dirs() {
    let tmp = TempDir::new().unwrap();
    make_tree(
        tmp.path(),
        "111",
        &["Profile1", "Profile2"],
        &[&["a.run"], &["b.run"]],
    );

    unsafe { env::set_var("STS2_BASE_DIR", tmp.path()) };
    let dirs = discover_save_dirs().unwrap();
    unsafe { env::remove_var("STS2_BASE_DIR") };

    assert_eq!(dirs.len(), 2);
    assert!(dirs.iter().all(|d| d.ends_with("saves/history") || d.ends_with("saves\\history")));
}

// ---- ClientState ----

#[test]
fn state_round_trip() {
    let tmp = TempDir::new().unwrap();
    {
        let mut state = ClientState::load(tmp.path()).unwrap();
        assert!(!state.contains("run1"));
        state.mark_uploaded("run1".to_string()).unwrap();
        assert!(state.contains("run1"));
    }
    // Reload from disk
    let state = ClientState::load(tmp.path()).unwrap();
    assert!(state.contains("run1"));
}

#[test]
fn state_deduplicates() {
    let tmp = TempDir::new().unwrap();
    let mut state = ClientState::load(tmp.path()).unwrap();
    state.mark_uploaded("run1".to_string()).unwrap();
    state.mark_uploaded("run1".to_string()).unwrap(); // no-op
    let state2 = ClientState::load(tmp.path()).unwrap();
    assert!(state2.contains("run1"));
}

// ---- discover_existing_run_records (integration-ish) ----

#[test]
fn discover_finds_runs_across_profiles() {
    let tmp = TempDir::new().unwrap();
    make_tree(
        tmp.path(),
        "7654321",
        &["Profile1", "Profile2"],
        &[&["r1.run", "r2.run"], &["r3.run"]],
    );

    // Point the env var at our temp tree
    unsafe { env::set_var("STS2_BASE_DIR", tmp.path()) };
    let records = discover_existing_run_records().unwrap();
    unsafe { env::remove_var("STS2_BASE_DIR") };

    assert_eq!(records.len(), 3);
    let ids: HashSet<_> = records.iter().map(|r| r.id.clone()).collect();
    assert!(ids.contains("7654321:Profile1:r1.run"));
    assert!(ids.contains("7654321:Profile1:r2.run"));
    assert!(ids.contains("7654321:Profile2:r3.run"));
}

#[test]
fn discover_returns_empty_when_no_steam_dir() {
    let tmp = TempDir::new().unwrap();
    // base dir exists but has no "steam" subdirectory
    unsafe { env::set_var("STS2_BASE_DIR", tmp.path()) };
    let records = discover_existing_run_records().unwrap();
    unsafe { env::remove_var("STS2_BASE_DIR") };

    assert!(records.is_empty());
}

#[test]
fn discover_skips_non_profile_dirs() {
    let tmp = TempDir::new().unwrap();
    make_tree(
        tmp.path(),
        "111",
        &["Profile1"],
        &[&["g.run"]],
    );
    // Add a non-profile sibling directory with a .run file
    let settings_history = tmp.path()
        .join("steam")
        .join("111")
        .join("settings")
        .join("saves")
        .join("history");
    fs::create_dir_all(&settings_history).unwrap();
    fs::write(settings_history.join("sneaky.run"), "data").unwrap();

    unsafe { env::set_var("STS2_BASE_DIR", tmp.path()) };
    let records = discover_existing_run_records().unwrap();
    unsafe { env::remove_var("STS2_BASE_DIR") };

    assert_eq!(records.len(), 1);
    assert_eq!(records[0].file_name, "g.run");
}