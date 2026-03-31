// TODO: integrate `notify` crate for filesystem watching
//
// Target API:
//
//   pub fn start_watchers(
//       save_dirs: &[PathBuf],
//       tx: Sender<PathBuf>,
//   ) -> notify::Result<Vec<RecommendedWatcher>>
//
// Each watcher monitors a `saves/history` directory and sends new/changed
// `.run` file paths through the channel.
