pub mod service;
#[derive(Debug, PartialEq)] pub enum TagError { Empty, InvalidCharacter }
pub fn normalize_tag(raw: &str) -> Result<String, TagError> {
 let s=raw.trim(); if s.is_empty() { return Err(TagError::Empty); }
 if !s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_') { return Err(TagError::InvalidCharacter); }
 Ok(s.to_ascii_lowercase())
}
