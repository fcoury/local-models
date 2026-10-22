pub mod service;
pub fn normalize_tag(raw: &str) -> String { raw.trim().to_ascii_lowercase() }
