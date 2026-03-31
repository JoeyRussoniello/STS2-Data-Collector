use std::collections::HashMap;
use std::fs;
use std::io;

use base64::Engine;
use base64::engine::general_purpose::STANDARD as BASE64;
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
        Self {
            client: Client::new(),
            base_url: DEFAULT_BASE_URL.to_string(),
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
    /// Reads the .run file, base64-encodes it, and PUTs it as JSON.
    pub fn upload_record(&self, record: &RunFileRecord) -> io::Result<()> {
        let raw_bytes = fs::read(&record.path)?;
        let encoded = BASE64.encode(&raw_bytes);

        let mut data = HashMap::new();
        data.insert("raw_base64", Value::String(encoded));
        data.insert(
            "file_size_bytes",
            Value::Number(record.size_bytes.into()),
        );

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
