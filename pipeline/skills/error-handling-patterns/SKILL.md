---
name: error-handling-patterns
description: Master error handling patterns across languages including exceptions, Result types, error propagation, and graceful degradation to build resilient applications. Use when implementing error handling, designing APIs, or improving application reliability.
---

# Error Handling Patterns

Build resilient applications with robust error handling strategies that gracefully handle failures and provide excellent debugging experiences.

## When to Use This Skill

- Implementing error handling in new code
- Refactoring existing error handling
- Designing API error responses
- Building resilient microservices
- Setting up monitoring and alerting
- Handling third-party service failures
- Implementing retry and fallback logic
- Writing safety-critical code

## Core Concepts

### 1. Error Types

**Recoverable Errors**: Can be handled gracefully (network timeout, file not found)
**Unrecoverable Errors**: Cannot be handled (out of memory, hardware failure)

Recoverable errors should be caught and handled. Unrecoverable errors should crash loudly.

### 2. Error Handling Strategies

- **Fail Fast**: Detect and report errors as early as possible
- **Graceful Degradation**: Continue serving with reduced functionality
- **Retry**: Temporary failures may succeed on retry
- **Fallback**: Provide alternative when primary path fails
- **Circuit Breaker**: Stop calling failing services to allow recovery
- **Bulkhead**: Isolate failures to prevent cascading

## Language-Specific Patterns

### Python Error Handling

#### Basic Exception Handling

```python
import logging

logger = logging.getLogger(__name__)

def read_user_data(user_id: str) -> dict:
    """Read user data with proper error handling."""
    try:
        response = api.get(f"/users/{user_id}")
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx
        return response.json()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"User not found: {user_id}")
            return None
        elif e.response.status_code == 429:
            logger.warning("Rate limited")
            raise ServiceUnavailable("API rate limit exceeded")
        else:
            logger.error(f"API error fetching user {user_id}: {e}")
            raise
    except requests.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise ServiceUnavailable("Unable to connect to API")
    except Exception as e:
        logger.exception(f"Unexpected error fetching user {user_id}")
        raise
```

#### Custom Exception Hierarchy

```python
class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        super().__init__(self.message)

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        super().__init__(
            message=f"{resource} not found: {id}",
            code="NOT_FOUND"
        )

class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error on {field}: {message}",
            code="VALIDATION_ERROR"
        )
        self.field = field

class ServiceUnavailable(AppError):
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE"
        )
```

#### Context Managers for Resource Management

```python
from contextlib import contextmanager

@contextmanager
def managed_database_connection(connection_string: str):
    """Context manager that ensures database connection is properly closed."""
    conn = None
    try:
        conn = create_connection(connection_string)
        yield conn
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass  # Log and ignore close errors


# Usage
with managed_database_connection("postgresql://localhost/db") as conn:
    conn.execute("SELECT * FROM users")
# Connection is automatically closed, even if an error occurs
```

#### Try/Except/Else/Finally

```python
def process_file(filepath: str) -> dict:
    """Process a file with complete try/except/else/finally."""
    file = None
    try:
        file = open(filepath, 'r')
        data = file.read()
        result = parse_data(data)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except PermissionError:
        logger.error(f"Permission denied: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        raise ValidationError("file", "Invalid JSON format")
    else:
        # Executed only if no exception occurred
        logger.info(f"Successfully processed {filepath}")
        return result
    finally:
        # Always executed, even on exceptions
        if file:
            file.close()
```

### TypeScript/JavaScript Error Handling

#### Custom Error Classes

```typescript
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string = 'UNKNOWN_ERROR',
    public readonly statusCode: number = 500
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(
      `${resource} not found: ${id}`,
      'NOT_FOUND',
      404
    );
  }
}

export class ValidationError extends AppError {
  constructor(field: string, message: string) {
    super(
      `Validation error on ${field}: ${message}`,
      'VALIDATION_ERROR',
      422
    );
  }
}
```

#### Async Error Handling

```typescript
// Wrapper for async route handlers
export function asyncHandler(fn: RequestHandler): RequestHandler {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

// Usage in Express
app.get(
  '/users/:id',
  asyncHandler(async (req, res) => {
    const user = await userService.findById(req.params.id);
    if (!user) {
      throw new NotFoundError('User', req.params.id);
    }
    res.json(user);
  })
);

// Global error handler middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: err.code,
      message: err.message,
    });
  }

  // Unexpected error
  logger.error('Unhandled error', { error: err, stack: err.stack });
  return res.status(500).json({
    error: 'INTERNAL_ERROR',
    message: 'An unexpected error occurred',
  });
});
```

#### Try/Catch with Async/Await

```typescript
async function fetchUserData(userId: string): Promise<UserData> {
  try {
    const response = await fetch(`/api/users/${userId}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new AppError(
        error.message || 'Failed to fetch user',
        error.code || 'API_ERROR',
        response.status
      );
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof AppError) {
      throw error;  // Re-throw known errors
    }
    
    // Network errors
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      throw new ServiceUnavailable('Network error');
    }
    
    // Unknown errors
    logger.error('Unexpected error in fetchUserData', { error });
    throw new AppError('An unexpected error occurred');
  }
}
```

## Advanced Patterns

### Pattern 1: Retry with Exponential Backoff

```python
import time
import random
from functools import wraps

def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError)
):
    """Decorator with exponential backoff and jitter."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (backoff_factor ** (attempt - 1)),
                        max_delay
                    )
                    
                    # Add jitter (±25%)
                    if jitter:
                        delay *= 1 + random.uniform(-0.25, 0.25)
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
            
            raise last_exception  # Should not reach here
        return wrapper
    return decorator


# Usage
@retry(max_attempts=3, base_delay=1.0)
def fetch_data(url: str) -> dict:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()
```

### Pattern 2: Circuit Breaker

```python
from enum import Enum
import time
from functools import wraps

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_requests: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_requests = half_open_max_requests
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_requests = 0
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_requests = 0
                else:
                    raise CircuitBreakerOpenError("Circuit breaker is open")
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_requests >= self.half_open_max_requests:
                    raise CircuitBreakerOpenError("Too many half-open requests")
                self.half_open_requests += 1
            
            try:
                result = func(*args, **kwargs)
                
                # Success - reset circuit
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                
                raise
        
        return wrapper


# Usage
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

@circuit_breaker
def call_external_api():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()
```

### Pattern 3: Graceful Degradation

```python
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class ServiceWithFallback:
    def __init__(self):
        self.cache = {}
    
    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Get user profile with graceful degradation."""
        
        # Primary path: try cache first
        if user_id in self.cache:
            return self.cache[user_id]
        
        try:
            # Primary path: fetch from primary API
            profile = self._fetch_from_primary(user_id)
            self.cache[user_id] = profile
            return profile
        except PrimaryServiceError:
            logger.warning(f"Primary service failed for user {user_id}")
        
        try:
            # Fallback path: fetch from secondary API
            profile = self._fetch_from_secondary(user_id)
            self.cache[user_id] = profile
            return profile
        except SecondaryServiceError:
            logger.warning(f"Secondary service also failed for user {user_id}")
        
        # Last resort: return cached data (even if stale)
        stale_data = self._get_stale_cache(user_id)
        if stale_data:
            logger.info(f"Returning stale data for user {user_id}")
            return stale_data
        
        # Complete failure
        logger.error(f"Failed to get profile for user {user_id}")
        return None
    
    def _fetch_from_primary(self, user_id: str) -> dict:
        # Primary API call
        pass
    
    def _fetch_from_secondary(self, user_id: str) -> dict:
        # Fallback API call
        pass
    
    def _get_stale_cache(self, user_id: str) -> Optional[dict]:
        # Get expired cache entry
        pass
```

### Pattern 4: Result Monad Pattern

```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Callable

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

@dataclass
class Result(Generic[T]):
    """Result type for explicit error handling."""
    value: Optional[T] = None
    error: Optional[Exception] = None
    
    @classmethod
    def ok(cls, value: T) -> 'Result[T]':
        return cls(value=value, error=None)
    
    @classmethod
    def err(cls, error: Exception) -> 'Result[T]':
        return cls(value=None, error=error)
    
    def is_ok(self) -> bool:
        return self.error is None
    
    def is_err(self) -> bool:
        return self.error is not None
    
    def unwrap(self) -> T:
        if self.error:
            raise self.error
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        return self.value if self.is_ok() else default
    
    def map(self, fn: Callable[[T], T]) -> 'Result[T]':
        if self.is_ok():
            try:
                return Result.ok(fn(self.value))
            except Exception as e:
                return Result.err(e)
        return self
    
    def map_err(self, fn: Callable[[Exception], Exception]) -> 'Result[T]':
        if self.is_err():
            return Result.err(fn(self.error))
        return self


# Usage
def divide(a: float, b: float) -> Result[float]:
    """Divide a by b, returning Result type."""
    if b == 0:
        return Result.err(ValueError("Cannot divide by zero"))
    if not isinstance(a, (int, float)):
        return Result.err(TypeError("a must be a number"))
    return Result.ok(a / b)


result = divide(10, 2)
if result.is_ok():
    print(f"Result: {result.unwrap()}")
else:
    print(f"Error: {result.error}")


# Chaining with map
final = divide(10, 2).map(lambda x: x * 2).map(lambda x: x + 1)
print(final.unwrap())  # 11.0
```

### Pattern 5: Structured Logging

```python
import structlog

logger = structlog.get_logger()

def process_order(order_id: str, user_id: str):
    """Process order with structured logging."""
    log = logger.bind(order_id=order_id, user_id=user_id)
    
    try:
        log.info("Starting order processing")
        
        # Business logic
        order = fetch_order(order_id)
        log.debug("Order fetched", order_status=order.status)
        
        result = process_payment(order)
        log.info("Payment processed", payment_id=result.id)
        
        return result
    except PaymentError as e:
        log.error("Payment failed", error=str(e), error_code=e.code)
        raise
    except Exception as e:
        log.exception("Unexpected error in order processing")
        raise
```

## Error Handling Best Practices

1. **Fail Fast**: Validate inputs early, don't let bad data propagate
2. **Never Swallow Exceptions**: Don't use empty except blocks
3. **Log at Appropriate Levels**: DEBUG for details, INFO for normal, ERROR for failures
4. **Include Context**: Always log relevant identifiers (user_id, order_id)
5. **Use Custom Exceptions**: Create domain-specific exception hierarchy
6. **Document Error Conditions**: Document what exceptions a function can raise
7. **Graceful Degradation**: Handle failures without crashing the whole system
8. **Consistent API Errors**: Use standard error response formats
9. **Test Error Paths**: Test both success and failure scenarios
10. **Monitor Errors**: Set up alerting on error rates and patterns

## Anti-Patterns

- **Bare Except**: `except:` catches everything including SystemExit, KeyboardInterrupt
- **Silent Catch**: Empty except block that ignores the error
- **Too Broad**: Catching Exception when you should catch specific types
- **Swallow and Continue**: Catching error but continuing with corrupted state
- **Return Error Codes**: Returning special values instead of raising exceptions
- **Log and Re-raise in Same Function**: Either handle the error or let it propagate, not both
- **Ignoring Async Errors**: Not handling Promise rejections or async exceptions
