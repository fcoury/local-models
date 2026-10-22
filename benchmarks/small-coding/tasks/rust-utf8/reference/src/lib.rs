pub fn truncate_utf8(input: &str, max_bytes: usize) -> &str {
    let mut end = max_bytes.min(input.len());
    while !input.is_char_boundary(end) { end -= 1; }
    &input[..end]
}
