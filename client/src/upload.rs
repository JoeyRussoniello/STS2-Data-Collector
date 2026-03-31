// TODO: HTTP upload logic
//
// Target API:
//
//   pub fn upload_record(record: &RunFileRecord) -> io::Result<()>
//
// POST the run file to the collection server. Steam ID hashing happens
// server-side, so this transmits the raw record.
