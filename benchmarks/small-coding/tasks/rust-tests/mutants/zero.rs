pub fn parse_port(s: &str) -> Option<u16> {
    if s.is_empty() || !s.bytes().all(|b| b.is_ascii_digit()) { return None; }
    let port = s.parse::<u16>().ok()?;
    Some(port)
}
