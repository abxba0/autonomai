"""
Example workflow step plugin.

This plugin demonstrates how to create custom workflow step executors
that can be used by the WorkflowOrchestrator.
"""

from typing import Optional, Dict, Any
from src.plugins import WorkflowStepPlugin, PluginMetadata, PluginConfig
from src.models.workflow import WorkflowStep, StepStatus


class DataTransformStepPlugin(WorkflowStepPlugin):
    """
    Plugin for executing data transformation steps in workflows.
    
    This plugin handles steps of type "data_transform" and applies
    various data transformations based on step configuration.
    """
    
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="data_transform_step",
            version="1.0.0",
            author="AutonomAI Team",
            description="Executes data transformation workflow steps",
            plugin_type="workflow_step",
            tags=["workflow", "data-processing", "transformation"],
        )
    
    def can_execute(self, step: WorkflowStep) -> bool:
        """Check if this plugin can execute the given step"""
        return hasattr(step, 'step_type') and step.step_type == "data_transform"
    
    def validate_step(self, step: WorkflowStep) -> tuple[bool, Optional[str]]:
        """Validate that the step has required configuration"""
        if not hasattr(step, 'inputs') or not step.inputs:
            return False, "Step must have inputs defined"
        
        if 'data' not in step.inputs:
            return False, "Step must have 'data' in inputs"
        
        # Check for transformation type in step description or metadata
        transform_type = step.description.split(":")[0].lower() if ":" in step.description else None
        
        valid_transforms = ["uppercase", "lowercase", "reverse", "filter", "map"]
        if transform_type and transform_type not in valid_transforms:
            return False, f"Unknown transform type: {transform_type}"
        
        return True, None
    
    def execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> tuple[StepStatus, Dict[str, Any]]:
        """
        Execute the data transformation step.
        """
        try:
            # Validate step
            is_valid, error = self.validate_step(step)
            if not is_valid:
                return StepStatus.FAILED, {"error": error}
            
            # Get input data
            data = step.inputs.get("data", "")
            
            # Determine transformation type from step description
            transform_type = step.description.split(":")[0].lower() if ":" in step.description else "uppercase"
            
            # Apply transformation
            result = self._apply_transform(data, transform_type)
            
            return StepStatus.COMPLETED, {
                "transformed_data": result,
                "transform_type": transform_type,
                "original_length": len(str(data)),
                "result_length": len(str(result)),
            }
        
        except Exception as e:
            return StepStatus.FAILED, {
                "error": str(e),
                "step_id": step.step_id,
            }
    
    def _apply_transform(self, data: Any, transform_type: str) -> Any:
        """Apply the specified transformation to the data"""
        if isinstance(data, str):
            if transform_type == "uppercase":
                return data.upper()
            elif transform_type == "lowercase":
                return data.lower()
            elif transform_type == "reverse":
                return data[::-1]
            elif transform_type == "filter":
                # Example: filter out digits
                return ''.join(c for c in data if not c.isdigit())
            elif transform_type == "map":
                # Example: replace spaces with underscores
                return data.replace(" ", "_")
        
        return data


class CustomAPIStepPlugin(WorkflowStepPlugin):
    """
    Plugin for making custom API calls in workflows.
    
    This plugin handles steps of type "custom_api" and makes
    HTTP requests based on step configuration.
    """
    
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="custom_api_step",
            version="1.0.0",
            author="AutonomAI Team",
            description="Executes custom API call workflow steps",
            plugin_type="workflow_step",
            tags=["workflow", "api", "http"],
            dependencies=["requests"],  # Optional dependency
        )
    
    def can_execute(self, step: WorkflowStep) -> bool:
        """Check if this plugin can execute the given step"""
        return hasattr(step, 'step_type') and step.step_type == "custom_api"
    
    def validate_step(self, step: WorkflowStep) -> tuple[bool, Optional[str]]:
        """Validate API step configuration"""
        if not hasattr(step, 'inputs') or not step.inputs:
            return False, "Step must have inputs defined"
        
        required_fields = ["url", "method"]
        for field in required_fields:
            if field not in step.inputs:
                return False, f"Step must have '{field}' in inputs"
        
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if step.inputs["method"].upper() not in valid_methods:
            return False, f"Invalid HTTP method: {step.inputs['method']}"
        
        return True, None
    
    def execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> tuple[StepStatus, Dict[str, Any]]:
        """
        Execute the API call step.
        
        Note: This is a demonstration - in production, you'd use
        the requests library and handle errors properly.
        """
        try:
            # Validate step
            is_valid, error = self.validate_step(step)
            if not is_valid:
                return StepStatus.FAILED, {"error": error}
            
            # For demonstration, we'll simulate the API call
            url = step.inputs["url"]
            method = step.inputs["method"].upper()
            
            # In a real implementation:
            # import requests
            # response = requests.request(method, url, ...)
            
            # Simulated response
            simulated_response = {
                "status_code": 200,
                "data": {"message": f"Simulated {method} request to {url}"},
            }
            
            return StepStatus.COMPLETED, {
                "response": simulated_response,
                "url": url,
                "method": method,
            }
        
        except Exception as e:
            return StepStatus.FAILED, {
                "error": str(e),
                "step_id": step.step_id,
            }


# Example usage:
if __name__ == "__main__":
    from src.plugins import PluginManager
    from src.models.workflow import WorkflowStep
    
    # Create and register plugins
    manager = PluginManager()
    
    # Register data transform plugin
    transform_plugin = DataTransformStepPlugin(
        DataTransformStepPlugin.get_metadata(),
        PluginConfig(enabled=True, priority=100)
    )
    
    if manager.register_plugin(transform_plugin):
        print(f"✓ Plugin {transform_plugin.metadata.name} registered")
    
    # Register API plugin
    api_plugin = CustomAPIStepPlugin(
        CustomAPIStepPlugin.get_metadata(),
        PluginConfig(enabled=True, priority=100)
    )
    
    if manager.register_plugin(api_plugin):
        print(f"✓ Plugin {api_plugin.metadata.name} registered")
    
    # Example: Execute a step
    test_step = WorkflowStep(
        name="Demo Step",
        description="uppercase: Transform text to uppercase",
    )
    test_step.step_type = "data_transform"
    test_step.inputs = {"data": "hello plugin world"}
    
    executor = manager.find_workflow_step_executor(test_step)
    if executor:
        status, outputs = executor.execute_step(test_step, {})
        print(f"Step execution: {status.value}")
        print(f"Outputs: {outputs}")
