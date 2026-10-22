use std::collections::VecDeque;
/// Callers supply nondecreasing timestamps, a positive window and a fixed limit.
pub fn admit(events: &mut VecDeque<u64>, now: u64, window: u64, limit: usize) -> bool {
 while events.front().is_some_and(|&t| now.saturating_sub(t) >= window) { events.pop_front(); }
 if events.len() >= limit { return false; }
 events.push_back(now); true
}
