# Plugin System Architecture

## Overview

AutonomAI features a production-grade plugin system that enables third-party developers to extend the system with custom validators, optimizers, and workflow steps. The plugin system is designed with flexibility, safety, and ease of use in mind.

## Key Features

- **Multiple Discovery Mechanisms**: Load plugins from entry points, directories, or configuration files
- **Type-Safe**: Strong typing with Python type hints throughout
- **Lifecycle Management**: Complete plugin lifecycle (load, initialize, activate, cleanup)
- **Priority-Based Execution**: Control plugin execution order with priority settings
- **Event-Based Hooks**: Subscribe to plugin events for monitoring and integration
- **Configuration Support**: YAML/JSON configuration for plugin settings
- **Error Handling**: Robust error handling with detailed error messages

## Architecture

### Core Components

1. **BasePlugin**: Abstract base class for all plugins
2. **PluginRegistry**: Central registry managing all loaded plugins
3. **PluginLoader**: Discovers and loads plugins from various sources
4. **PluginManager**: High-level interface for plugin system operations

### Plugin Types

1. **ValidatorPlugin**: Extends validation capabilities
2. **OptimizerPlugin**: Adds custom failure analysis and optimization
3. **WorkflowStepPlugin**: Implements custom workflow step types
4. **FailureAnalyzerPlugin**: Specialized optimizer for pattern extraction

## Plugin Lifecycle

```
UNLOADED → LOADED → INITIALIZED → ACTIVE
                                    ↓
                                 ERROR
```

1. **UNLOADED**: Plugin not yet loaded
2. **LOADED**: Plugin class loaded and registered
3. **INITIALIZED**: Plugin `initialize()` called successfully
4. **ACTIVE**: Plugin enabled and ready for use
5. **ERROR**: Plugin encountered an error

## Creating a Plugin

### 1. Validator Plugin

```python
from src.plugins import ValidatorPlugin, PluginMetadata, PluginConfig
from src.core.validator import BaseValidator, ValidationResult

class MyValidatorPlugin(ValidatorPlugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="my_validator",
            version="1.0.0",
            author="Your Name",
            description="Description of your validator",
            plugin_type="validator",
            tags=["validation", "custom"],
        )
    
    def create_validator(self) -> BaseValidator:
        # Return your validator instance
        class MyValidator(BaseValidator):
            def validate(self, output, context=None):
                # Your validation logic
                passed = len(output) > 10
                return ValidationResult(
                    passed=passed,
                    validator_name=self.name,
                    error_message="Output too short" if not passed else None
                )
        
        return MyValidator("my_validator")
```

### 2. Optimizer Plugin

```python
from src.plugins import OptimizerPlugin, PluginMetadata
from src.models.failure import FailureEntry
from src.models.critic_response import CriticResponse

class MyOptimizerPlugin(OptimizerPlugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="my_optimizer",
            version="1.0.0",
            author="Your Name",
            description="Custom optimization logic",
            plugin_type="optimizer",
        )
    
    def can_handle(self, failure: FailureEntry) -> bool:
        # Return True if this optimizer can handle the failure
        return "specific_error" in failure.error_message
    
    def analyze_failure(
        self,
        failure: FailureEntry,
        current_instructions: str,
        context=None
    ) -> CriticResponse:
        # Analyze failure and return proposed changes
        return CriticResponse(
            should_update=True,
            confidence=0.8,
            proposed_changes="Add specific handling for...",
            reasoning="Analysis shows that...",
        )
```

### 3. Workflow Step Plugin

```python
from src.plugins import WorkflowStepPlugin, PluginMetadata
from src.models.workflow import WorkflowStep, StepStatus

class MyWorkflowStepPlugin(WorkflowStepPlugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="my_workflow_step",
            version="1.0.0",
            author="Your Name",
            description="Custom workflow step executor",
            plugin_type="workflow_step",
        )
    
    def can_execute(self, step: WorkflowStep) -> bool:
        # Check if this plugin can execute the step
        return step.step_type == "my_custom_type"
    
    def execute_step(self, step: WorkflowStep, context):
        # Execute the step and return status and outputs
        try:
            # Your execution logic here
            result = "success"
            
            return StepStatus.COMPLETED, {
                "result": result,
                "metadata": {...}
            }
        except Exception as e:
            return StepStatus.FAILED, {"error": str(e)}
```

## Loading Plugins

### Method 1: Entry Points (Recommended for Distribution)

In your `setup.py` or `pyproject.toml`:

```python
# setup.py
setup(
    name="my-autonomai-plugin",
    entry_points={
        "autonomai.plugins": [
            "my_plugin = my_package.plugin:MyPlugin",
        ],
    },
)
```

```toml
# pyproject.toml
[project.entry-points."autonomai.plugins"]
my_plugin = "my_package.plugin:MyPlugin"
```

### Method 2: Directory Scanning

```python
from pathlib import Path
from src.plugins import PluginManager

manager = PluginManager()
manager.discover_and_load_plugins(
    plugin_dirs=[Path("./plugins")]
)
```

### Method 3: Configuration File

Create `plugin_config.yaml`:

```yaml
plugins:
  - name: my_validator
    module: my_package.validator
    class: MyValidatorPlugin
    config:
      enabled: true
      priority: 50
      settings:
        option1: value1
        option2: value2
```

Load plugins:

```python
manager.discover_and_load_plugins(
    config_file=Path("./plugin_config.yaml")
)
```

### Method 4: Explicit Registration

```python
manager = PluginManager()
plugin = MyValidatorPlugin(
    MyValidatorPlugin.get_metadata(),
    PluginConfig(enabled=True, priority=100)
)
manager.register_plugin(plugin)
```

## Using Plugins

### Integrating with ValidationPipeline

```python
from src import SelfOptimizingSystem
from src.plugins import PluginManager

# Initialize system
system = SelfOptimizingSystem()
manager = PluginManager()

# Load plugins
manager.discover_and_load_plugins(
    plugin_dirs=[Path("./plugins")]
)

# Add plugin validators to pipeline
for validator in manager.get_validators_for_pipeline():
    system.validation_pipeline.add_validator(validator)
```

### Using Optimizers

```python
# Find optimizer for a specific failure
optimizer = manager.find_optimizer_for_failure(failure)
if optimizer:
    response = optimizer.analyze_failure(
        failure,
        current_instructions,
        context
    )
    if response.should_update:
        # Apply the proposed changes
        pass
```

### Using Workflow Steps

```python
# Find executor for a workflow step
executor = manager.find_workflow_step_executor(step)
if executor:
    status, outputs = executor.execute_step(step, context)
    if status == StepStatus.COMPLETED:
        # Process outputs
        pass
```

## Configuration

### Plugin Configuration Options

```python
from src.plugins import PluginConfig

config = PluginConfig(
    enabled=True,           # Enable/disable plugin
    priority=100,          # Lower = higher priority
    settings={             # Plugin-specific settings
        "option1": "value1",
        "option2": 42,
        "nested": {
            "key": "value"
        }
    }
)
```

Access settings in your plugin:

```python
def initialize(self):
    option1 = self.config.get("option1", "default")
    option2 = self.config.get("option2", 0)
    return True
```

## Plugin Management

### List Plugins

```python
# List all plugins
plugins = manager.list_plugins()
for plugin in plugins:
    print(f"{plugin['name']} v{plugin['version']}: {plugin['state']}")

# List plugins by type
validators = manager.list_plugins("validator")
```

### Enable/Disable Plugins

```python
# Disable a plugin
manager.disable_plugin("my_plugin")

# Enable a plugin
manager.enable_plugin("my_plugin")
```

### Unload Plugins

```python
# Unload a plugin
manager.unload_plugin("my_plugin")
```

## Best Practices

1. **Version Compatibility**: Specify `min_system_version` and `max_system_version` in metadata
2. **Error Handling**: Always wrap plugin logic in try-except blocks
3. **Configuration Validation**: Override `validate_config()` to validate settings
4. **Resource Cleanup**: Implement `cleanup()` to properly release resources
5. **Documentation**: Document configuration options and usage in plugin docstrings
6. **Testing**: Create comprehensive tests for your plugins
7. **Dependencies**: List all dependencies in plugin metadata
8. **Semantic Versioning**: Follow semver for plugin versions

## Security Considerations

1. **Input Validation**: Always validate inputs before processing
2. **Sandboxing**: Plugins run in the same process - use caution with untrusted code
3. **Resource Limits**: Be mindful of CPU and memory usage
4. **Error Reporting**: Don't expose sensitive information in error messages
5. **Permissions**: Document any file system or network access requirements

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Plugin State

```python
plugin = manager.registry.get("my_plugin")
print(f"State: {plugin.lifecycle_state}")
print(f"Error: {plugin.error_message}")
```

### Test Plugins in Isolation

```python
# Test plugin directly
plugin = MyPlugin(metadata, config)
success = plugin.initialize()
assert success, plugin.error_message
```

## Examples

See the `examples/plugins/` directory for complete examples:

- `keyword_validator_plugin.py`: Validator for keywords
- `failure_analyzer_plugin.py`: Pattern extraction from failures
- `workflow_step_plugin.py`: Custom workflow step executors

## API Reference

### BasePlugin

- `initialize() -> bool`: Initialize plugin
- `cleanup()`: Clean up resources
- `validate_config() -> (bool, Optional[str])`: Validate configuration
- `lifecycle_state: PluginLifecycle`: Current state
- `error_message: Optional[str]`: Error message if in ERROR state

### PluginManager

- `register_plugin(plugin) -> bool`: Register a plugin
- `get_validator_plugins() -> List[ValidatorPlugin]`: Get validator plugins
- `get_optimizer_plugins() -> List[OptimizerPlugin]`: Get optimizer plugins
- `get_workflow_step_plugins() -> List[WorkflowStepPlugin]`: Get workflow plugins
- `find_optimizer_for_failure(failure) -> Optional[OptimizerPlugin]`: Find optimizer
- `find_workflow_step_executor(step) -> Optional[WorkflowStepPlugin]`: Find executor
- `list_plugins(plugin_type=None) -> List[Dict]`: List plugins
- `enable_plugin(name) -> bool`: Enable plugin
- `disable_plugin(name) -> bool`: Disable plugin
- `unload_plugin(name) -> bool`: Unload plugin

## Support

For issues or questions about plugin development:

1. Check the examples in `examples/plugins/`
2. Review the tests in `tests/test_plugin_system.py`
3. Open an issue on GitHub
4. Consult the API documentation

## Contributing

We welcome plugin contributions! To contribute:

1. Follow the plugin development guidelines
2. Add comprehensive tests
3. Document your plugin thoroughly
4. Submit a pull request

## License

The plugin system is part of AutonomAI and is licensed under the MIT License.
