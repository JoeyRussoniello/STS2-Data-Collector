use std::fs;
use std::io;

use reqwest::blocking::Client;
use serde_json::Value;

use crate::record::RunFileRecord;

const DEFAULT_BASE_URL: &str = "https://sts2-data-collector-production.up.railway.app";
/// Baked in at compile time via `STS2_API_KEY=xxx cargo build --release`.
/// Falls back to reading the env var at runtime if not set at compile time.
const COMPILED_API_KEY: Option<&str> = option_env!("STS2_API_KEY");

/// Outcome of an upload attempt.
#[derive(Debug)]
pub enum UploadResult {
    /// Upload succeeded.
    Success,
    /// Transient failure (network, 429, 5xx) — worth retrying.
    Retryable(String),
    /// Permanent failure (4xx other than 429) — do not retry.
    Permanent(String),
}

pub struct Uploader {
    client: Client,
    base_url: String,
    api_key: String,
}

impl Uploader {
    pub fn new() -> Self {
        let base_url = std::env::var("STS2_SERVER_URL")
            .unwrap_or_else(|_| DEFAULT_BASE_URL.to_string());
        let api_key = std::env::var("STS2_API_KEY")
            .unwrap_or_else(|_| COMPILED_API_KEY.unwrap_or("").to_string());
        Self {
            client: Client::new(),
            base_url: base_url.trim_end_matches('/').to_string(),
            api_key,
        }
    }

    #[allow(dead_code)]
    pub fn with_base_url(base_url: &str) -> Self {
        let api_key = std::env::var("STS2_API_KEY")
            .unwrap_or_else(|_| COMPILED_API_KEY.unwrap_or("").to_string());
        Self {
            client: Client::new(),
            base_url: base_url.trim_end_matches('/').to_string(),
            api_key,
        }
    }

    /// Upload a run record to the backend.
    /// Reads the .run file (which is JSON), parses it, and POSTs it.
    /// The server generates the global run_id from the hashed steam_id.
    pub fn upload_record(&self, record: &RunFileRecord) -> UploadResult {
        let raw = match fs::read_to_string(&record.path) {
            Ok(s) => s,
            Err(e) => return UploadResult::Permanent(format!("Cannot read file: {e}")),
        };
        let data: Value = match serde_json::from_str(&raw) {
            Ok(v) => v,
            Err(e) => return UploadResult::Permanent(format!("Invalid JSON: {e}")),
        };

        let body = serde_json::json!({
            "steam_id": record.steam_id,
            "profile": record.profile,
            "file_name": record.file_name,
            "file_size": record.size_bytes,
            "data": data,
        });

        let url = format!("{}/runs", self.base_url);

        let response = match self
            .client
            .post(&url)
            .header("X-API-Key", &self.api_key)
            .json(&body)
            .send()
        {
            Ok(r) => r,
            Err(e) => return UploadResult::Retryable(format!("Network error: {e}")),
        };

        if response.status().is_success() {
            println!("  Uploaded: {}", record.id);
            UploadResult::Success
        } else {
            let status = response.status();
            let body = response
                .text()
                .unwrap_or_else(|_| "no response body".to_string());
            let msg = format!("Upload failed ({status}): {body}");

            if status.as_u16() == 429 || status.is_server_error() {
                UploadResult::Retryable(msg)
            } else {
                UploadResult::Permanent(msg)
            }
        }
    }

    /// Backwards-compatible wrapper that returns io::Result.
    /// Used by the old call sites during the transition.
    pub fn upload_record_io(&self, record: &RunFileRecord) -> io::Result<()> {
        match self.upload_record(record) {
            UploadResult::Success => Ok(()),
            UploadResult::Retryable(msg) | UploadResult::Permanent(msg) => {
                Err(io::Error::new(io::ErrorKind::Other, msg))
            }
        }
    }
}
