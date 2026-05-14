// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from aic_engine_interfaces:srv/ResetJoints.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "aic_engine_interfaces/srv/reset_joints.h"


#ifndef AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__STRUCT_H_
#define AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'joint_names'
#include "rosidl_runtime_c/string.h"
// Member 'initial_positions'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in srv/ResetJoints in the package aic_engine_interfaces.
typedef struct aic_engine_interfaces__srv__ResetJoints_Request
{
  rosidl_runtime_c__String__Sequence joint_names;
  rosidl_runtime_c__double__Sequence initial_positions;
} aic_engine_interfaces__srv__ResetJoints_Request;

// Struct for a sequence of aic_engine_interfaces__srv__ResetJoints_Request.
typedef struct aic_engine_interfaces__srv__ResetJoints_Request__Sequence
{
  aic_engine_interfaces__srv__ResetJoints_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} aic_engine_interfaces__srv__ResetJoints_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/ResetJoints in the package aic_engine_interfaces.
typedef struct aic_engine_interfaces__srv__ResetJoints_Response
{
  /// indicate successful reset
  bool success;
  rosidl_runtime_c__String message;
} aic_engine_interfaces__srv__ResetJoints_Response;

// Struct for a sequence of aic_engine_interfaces__srv__ResetJoints_Response.
typedef struct aic_engine_interfaces__srv__ResetJoints_Response__Sequence
{
  aic_engine_interfaces__srv__ResetJoints_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} aic_engine_interfaces__srv__ResetJoints_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  aic_engine_interfaces__srv__ResetJoints_Event__request__MAX_SIZE = 1
};
// response
enum
{
  aic_engine_interfaces__srv__ResetJoints_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/ResetJoints in the package aic_engine_interfaces.
typedef struct aic_engine_interfaces__srv__ResetJoints_Event
{
  service_msgs__msg__ServiceEventInfo info;
  aic_engine_interfaces__srv__ResetJoints_Request__Sequence request;
  aic_engine_interfaces__srv__ResetJoints_Response__Sequence response;
} aic_engine_interfaces__srv__ResetJoints_Event;

// Struct for a sequence of aic_engine_interfaces__srv__ResetJoints_Event.
typedef struct aic_engine_interfaces__srv__ResetJoints_Event__Sequence
{
  aic_engine_interfaces__srv__ResetJoints_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} aic_engine_interfaces__srv__ResetJoints_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__STRUCT_H_
