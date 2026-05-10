---
name: debugging-strategies
description: Master systematic debugging techniques, profiling tools, and root cause analysis to efficiently track down bugs across any codebase or technology stack. Use when investigating bugs, performance issues, or unexpected behavior.
---

# Debugging Strategies

Transform debugging from frustrating guesswork into systematic problem-solving with proven strategies, powerful tools, and methodical approaches.

## When to Use This Skill

- Investigating bugs and unexpected behavior
- Debugging production incidents
- Tracking down performance issues
- Debugging distributed systems
- Analyzing crash reports and logs
- Code review with debugging mindset
- Mentoring junior developers in debugging
- Setting up debugging infrastructure

## Core Principles

### 1. The Scientific Method

**Formulate Hypothesis → Predict → Test → Observe → Refine**

1. **Observe**: What exactly is happening? Gather data.
2. **Hypothesize**: What could cause this? List possibilities.
3. **Predict**: If hypothesis is right, what else should be true?
4. **Test**: Design experiment to validate hypothesis.
5. **Analyze**: Did results match prediction? If yes, found cause. If no, refine.

### 2. Reproduce First

**Never debug a bug you can't reproduce.**

- Get a minimal, reliable reproduction case
- Document exact steps to reproduce
- Note environment details (OS, versions, config)
- Test in clean environment if possible
- Simplify: remove variables until only essential remains

### 3. Isolate the Variable

**Change one thing at a time.**

- Keep a log of what you've tried
- Change only one variable between tests
- Record results before changing next variable
- Return to known state between experiments

### 4. Work Backward from the Symptom

**Start where things go wrong and trace backward.**

- What's the error message or symptom?
- What code path leads to this point?
- What inputs produce this output?
- What changed recently?

### 5. Work Forward from the Fault

**Start from the source of the problem and trace the impact forward.**

- What data enters the system?
- How is it transformed at each step?
- Where does it deviate from expectations?

## The 4-Phase Debugging Approach

### Phase 1: Understand (10-20% of time)

**Goal:** Understand the problem deeply before touching code.

```markdown
1. Read the error message COMPLETELY
2. Check logs, stack traces, and metrics
3. Understand the expected behavior
4. Document the actual behavior
5. Note the environment and recent changes
6. Search for known issues (GitHub issues, Stack Overflow)
7. Write down your assumptions
```

**Key Questions:**
- What changed since it last worked?
- Is this consistent or intermittent?
- Does it affect all users or just some?
- Can I reproduce it locally?

### Phase 2: Investigate (40-50% of time)

**Goal:** Gather data and narrow down the cause.

```markdown
### Data Gathering Techniques:

1. **Log Analysis**
   - Check application logs
   - Check system logs (journalctl, syslog)
   - Check browser console (for web apps)

2. **Instrumentation**
   - Add strategic print/log statements
   - Use debuggers (pdb, gdb, Chrome DevTools)
   - Add timing measurements

3. **Reproduction**
   - Write a unit test that demonstrates the bug
   - Create minimal reproducer
   - Test with varying inputs

4. **Isolation**
   - Comment out sections to narrow scope
   - Test components in isolation
   - Use binary search on commits (git bisect)
```

**Progressive Narrowing:**

Start broad, get specific:

1. Which component? (Frontend? Backend? Database?)
2. Which module/function?
3. Which line of code?
4. Which data/input value?

### Phase 3: Fix (20-30% of time)

**Goal:** Implement and verify the fix.

```markdown
1. **Understand Root Cause First**
   - Don't fix symptoms, fix the cause
   - Verify your understanding of the cause
   - Consider other places the same pattern might fail

2. **Write the Fix**
   - Smallest possible change
   - Add tests that fail without the fix
   - Consider edge cases

3. **Verify the Fix**
   - Test with original reproduction case
   - Test with edge cases
   - Run existing tests
   - Test in staging if possible
```

### Phase 4: Learn (10% of time)

**Goal:** Prevent recurrence and share knowledge.

```markdown
1. **Document What You Learned**
   - Root cause in plain language
   - How you found it (for next time)
   - Any monitoring/alerting gaps

2. **Prevent Recurrence**
   - Add regression tests
   - Add input validation if needed
   - Add error handling if missing
   - Improve error messages

3. **Share Knowledge**
   - Postmortem if production incident
   - Team knowledge base entry
   - Update runbooks if applicable
```

## Debugging Tools & Techniques

### Technique 1: Print Debugging (Simple but Effective)

```python
# Strategic logging - log inputs and outputs
def process_order(order_id: str) -> dict:
    logger.debug(f"Processing order: {order_id}")  # Log input
    
    order = fetch_order(order_id)
    logger.debug(f"Fetched order: {order}")  # Log intermediate state
    
    if not order:
        logger.error(f"Order not found: {order_id}")
        return {"error": "Order not found"}
    
    result = transform_order(order)
    logger.debug(f"Transformed order: {result}")  # Log output
    
    return result
```

### Technique 2: Using pytest for Debugging

```python
# Write a focused test to reproduce the bug
def test_process_order_invalid_id():
    """Reproduce bug with empty order ID."""
    result = process_order("")
    assert result == {"error": "Invalid order ID"}

# Run specific test with verbose output
# pytest test_debug.py::test_process_order_invalid_id -vvs
```

### Technique 3: Python pdb Debugger

```python
import pdb

def complex_function(data):
    # Set breakpoint
    pdb.set_trace()
    
    # Now you can:
    # n - next line
    # s - step into function
    # c - continue to next breakpoint
    # p variable - print variable
    # l - show current line context
    # q - quit debugger
    
    result = process_data(data)
    return result
```

### Technique 4: Binary Search with git bisect

```bash
# Start bisect
git bisect start
git bisect bad          # Current commit is bad
git bisect good v1.0    # v1.0 was working

# Git checks out middle commit
# Test it and mark
git bisect good         # If this commit works
git bisect bad          # If this commit has the bug

# Repeat until single commit identified
git bisect reset        # Clean up when done
```

### Technique 5: Chrome DevTools Debugging

```javascript
// Set breakpoint in code
debugger;

// Examine scope, call stack, and variables
// Use console for live inspection
console.log(data);
console.table(users);
console.time('operation');
// ... code ...
console.timeEnd('operation');

// Watch expressions in DevTools
// Element inspection for DOM issues
```

## Common Bug Patterns

### Pattern 1: Off-by-One Errors

```python
# ❌ Bug - misses last element
for i in range(len(items)):  # Stops at len-1... wait, that's correct
    pass

# ❌ Bug - off-by-one
for i in range(1, len(items)):  # Skips first element (index 0)
    print(items[i])

# ✅ Correct
for i in range(len(items)):
    print(items[i])
```

### Pattern 2: Race Conditions

```python
import threading
from typing import List

class Counter:
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()
    
    def increment(self):
        # ❌ Not thread-safe
        self.value += 1   # Read + modify + write (not atomic)
        
        # ✅ Thread-safe
        with self._lock:
            self.value += 1
```

### Pattern 3: Silent Failure

```python
# ❌ Bug - silently swallows errors
try:
    result = risky_operation()
except:
    pass  # Never know something went wrong

# ✅ Proper error handling
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise  # Re-raise if can't handle
```

### Pattern 4: State Mutation

```python
# ❌ Bug - mutating shared state
default_config = {"debug": False, "timeout": 30}

def process(config):
    config["debug"] = True  # Mutates default!
    return do_work(config)

# ✅ Safe - create copy
def process(config):
    cfg = {**config, "debug": True}
    return do_work(cfg)
```

## Advanced Debugging Techniques

### Network Debugging

```bash
# Check if service is listening
netstat -tlnp | grep 8080
ss -tlnp | grep 8080

# Trace HTTP requests
curl -v http://localhost:8080/api/health

# Monitor network traffic
tcpdump -i any port 8080 -X
```

### Performance Debugging

```python
import cProfile
import pstats

# Profile a function
cProfile.run('my_function()', 'profile_stats')

# Analyze results
p = pstats.Stats('profile_stats')
p.sort_stats('cumulative').print_stats(20)
```

### Database Debugging

```sql
-- Check slow queries
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- Check active connections
SELECT * FROM pg_stat_activity;

-- Check locks
SELECT * FROM pg_locks WHERE NOT granted;
```

## Debugging Checklist

### Initial Triage
- [ ] Can I reproduce the issue?
- [ ] What changed recently?
- [ ] Is this a known issue?
- [ ] Is this a regression?
- [ ] What's the severity/impact?

### During Investigation
- [ ] Have I read the FULL error message?
- [ ] Have I checked all logs?
- [ ] Have I simplified the reproduction?
- [ ] Am I changing one variable at a time?
- [ ] Have I used git bisect for regressions?

### Before Fixing
- [ ] Do I understand the root cause?
- [ ] Does my fix address the cause, not the symptom?
- [ ] Have I written a test that fails without the fix?
- [ ] Have I checked for similar patterns in the codebase?

### After Fixing
- [ ] Do existing tests pass?
- [ ] Have I added regression tests?
- [ ] Have I documented the root cause?
- [ ] Could this happen elsewhere?

## Common Debugging Pitfalls

- **Assuming**: Don't assume - verify every assumption
- **Confirmation Bias**: Don't just look for evidence that supports your theory
- **Premature Fixing**: Fix the cause, not the symptom
- **Changing Too Much**: Change one thing at a time
- **Not Taking Notes**: Document what you've tried
- **Skipping Reproduction**: Never fix a bug you can't reproduce
- **Ignoring the Obvious**: Sometimes it's a typo, not a complex issue
- **Not Leveraging Tools**: Learn your debugger, profiler, and bisect
