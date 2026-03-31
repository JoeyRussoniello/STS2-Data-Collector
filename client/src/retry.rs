use std::time::{Duration, Instant};

use crate::record::RunFileRecord;

const MAX_RETRIES: u32 = 5;
const BASE_DELAY: Duration = Duration::from_secs(1);
const MAX_DELAY: Duration = Duration::from_secs(32);

/// An entry in the retry queue: a failed upload waiting for its next attempt.
#[derive(Debug, Clone)]
pub struct RetryEntry {
    pub record: RunFileRecord,
    pub attempts: u32,
    pub next_attempt: Instant,
}
impl RetryEntry {
    pub fn new(record: RunFileRecord) -> Self{
        return Self{
            record,
            attempts: 1,
            next_attempt: Instant::now() + BASE_DELAY
        }
    }

    fn calculate_delay(&self) -> Duration{
        // Compute exponential backoff delay capped at MAX_DELAY.
        let multiplier = 1u64.checked_shl(self.attempts.saturating_sub(1)).unwrap_or(u64::MAX);
        let secs = BASE_DELAY.as_secs().saturating_mul(multiplier);
        Duration::from_secs(secs).min(MAX_DELAY)
    }

    pub fn increment_attempt(&mut self) {
        self.attempts += 1;
        let delay = self.calculate_delay();
        self.next_attempt = Instant::now() + delay;
    }

    pub fn is_over_max_retries(&self) -> bool {
        return self.attempts > MAX_RETRIES 
    }
}

/// A queue of failed uploads with exponential backoff.
pub struct RetryQueue {
    entries: Vec<RetryEntry>,
}

impl RetryQueue {
    pub fn new() -> Self {
        Self {
            entries: Vec::new(),
        }
    }

    /// Push a failed record into the retry queue (first failure).
    pub fn push(&mut self, record: RunFileRecord) {
        let entry = RetryEntry::new(record);
        self.entries.push(entry);
    }

    /// Re-enqueue an entry after another failed attempt, with increased backoff.
    /// Returns `false` if the entry has exhausted its retries (not re-enqueued).
    pub fn repush(&mut self, mut entry: RetryEntry) -> bool {
        entry.increment_attempt();
        if entry.is_over_max_retries(){
            return false;
        }
        self.entries.push(entry);
        true
    }

    /// Drain all entries whose next_attempt time has passed.
    pub fn drain_ready(&mut self) -> Vec<RetryEntry> {
        let now = Instant::now();
        let mut ready = Vec::new();
        self.entries.retain(|e| {
            if e.next_attempt <= now {
                ready.push(e.clone());
                false
            } else {
                true
            }
        });
        ready
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }
}


