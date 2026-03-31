use std::fs;
use std::io;

use reqwest::blocking::Client;
use serde_json::Value;

use crate::record::RunFileRecord;

const DEFAULT_BASE_URL: &str = "http://localhost:8000";

pub struct Uploader {
    client: Client,
    base_url: String,
}

impl Uploader {
    pub fn new() -> Self {
        let base_url = std::env::var("STS2_SERVER_URL")
            .unwrap_or_else(|_| DEFAULT_BASE_URL.to_string());
        Self {
            client: Client::new(),
            base_url: base_url.trim_end_matches('/').to_string(),
        }
    }

    #[allow(dead_code)]
    pub fn with_base_url(base_url: &str) -> Self {
        Self {
            client: Client::new(),
            base_url: base_url.trim_end_matches('/').to_string(),
        }
    }

    /// Upload a run record to the backend.
    /// Reads the .run file (which is JSON), parses it, and PUTs it directly.
    pub fn upload_record(&self, record: &RunFileRecord) -> io::Result<()> {
        let raw = fs::read_to_string(&record.path)?;
        let data: Value = serde_json::from_str(&raw).map_err(|e| {
            io::Error::new(
                io::ErrorKind::InvalidData,
                format!("Failed to parse .run file as JSON: {e}"),
            )
        })?;

        let body = serde_json::json!({
            "steam_id": record.steam_id,
            "profile": record.profile,
            "file_name": record.file_name,
            "file_size": record.size_bytes,
            "data": data,
        });

        let url = format!("{}/runs/{}", self.base_url, record.id);

        let response = self
            .client
            .put(&url)
            .json(&body)
            .send()
            .map_err(|e| io::Error::new(io::ErrorKind::ConnectionRefused, e.to_string()))?;

        if response.status().is_success() {
            println!("  Uploaded: {}", record.id);
            Ok(())
        } else {
            let status = response.status();
            let body = response
                .text()
                .unwrap_or_else(|_| "no response body".to_string());
            Err(io::Error::new(
                io::ErrorKind::Other,
                format!("Upload failed ({}): {}", status, body),
            ))
        }
    }
}
