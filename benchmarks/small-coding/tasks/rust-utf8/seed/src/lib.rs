/// Longest prefix whose UTF-8 encoding fits max_bytes. Never allocate or panic.
pub fn truncate_utf8(input: &str, max_bytes: usize) -> &str {
    &input[..input.len().min(max_bytes)]
}
