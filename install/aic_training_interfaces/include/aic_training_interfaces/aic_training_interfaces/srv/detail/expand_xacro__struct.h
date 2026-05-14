// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from aic_training_interfaces:srv/ExpandXacro.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "aic_training_interfaces/srv/expand_xacro.h"


#ifndef AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__STRUCT_H_
#define AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'package_name'
// Member 'relative_path'
// Member 'xacro_arguments'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/ExpandXacro in the package aic_training_interfaces.
typedef struct aic_training_interfaces__srv__ExpandXacro_Request
{
  rosidl_runtime_c__String package_name;
  rosidl_runtime_c__String relative_path;
  rosidl_runtime_c__String__Sequence xacro_arguments;
} aic_training_interfaces__srv__ExpandXacro_Request;

// Struct for a sequence of aic_training_interfaces__srv__ExpandXacro_Request.
typedef struct aic_training_interfaces__srv__ExpandXacro_Request__Sequence
{
  aic_training_interfaces__srv__ExpandXacro_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} aic_training_interfaces__srv__ExpandXacro_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'xml'
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/ExpandXacro in the package aic_training_interfaces.
typedef struct aic_training_interfaces__srv__ExpandXacro_Response
{
  bool success;
  rosidl_runtime_c__String xml;
  rosidl_runtime_c__String message;
} aic_training_interfaces__srv__ExpandXacro_Response;

// Struct for a sequence of aic_training_interfaces__srv__ExpandXacro_Response.
typedef struct aic_training_interfaces__srv__ExpandXacro_Response__Sequence
{
  aic_training_interfaces__srv__ExpandXacro_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} aic_training_interfaces__srv__ExpandXacro_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  aic_training_interfaces__srv__ExpandXacro_Event__request__MAX_SIZE = 1
};
// response
enum
{
  aic_training_interfaces__srv__ExpandXacro_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/ExpandXacro in the package aic_training_interfaces.
typedef struct aic_training_interfaces__srv__ExpandXacro_Event
{
  service_msgs__msg__ServiceEventInfo info;
  aic_training_interfaces__srv__ExpandXacro_Request__Sequence request;
  aic_training_interfaces__srv__ExpandXacro_Response__Sequence response;
} aic_training_interfaces__srv__ExpandXacro_Event;

// Struct for a sequence of aic_training_interfaces__srv__ExpandXacro_Event.
typedef struct aic_training_interfaces__srv__ExpandXacro_Event__Sequence
{
  aic_training_interfaces__srv__ExpandXacro_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} aic_training_interfaces__srv__ExpandXacro_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__STRUCT_H_
