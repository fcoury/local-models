pub fn parse_port(s: &str) -> Option<u16> {
    if s.is_empty() { return None; }
    let port = s.parse::<u16>().ok()?;
    (port != 0).then_some(port)
}
