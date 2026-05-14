// generated from rosidl_generator_c/resource/idl__type_support.h.em
// with input from aic_engine_interfaces:srv/ResetJoints.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "aic_engine_interfaces/srv/reset_joints.h"


#ifndef AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__TYPE_SUPPORT_H_
#define AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__TYPE_SUPPORT_H_

#include "rosidl_typesupport_interface/macros.h"

#include "aic_engine_interfaces/msg/rosidl_generator_c__visibility_control.h"

#ifdef __cplusplus
extern "C"
{
#endif

#include "rosidl_runtime_c/message_type_support_struct.h"

// Forward declare the get type support functions for this type.
ROSIDL_GENERATOR_C_PUBLIC_aic_engine_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
  rosidl_typesupport_c,
  aic_engine_interfaces,
  srv,
  ResetJoints_Request
)(void);

// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"

// Forward declare the get type support functions for this type.
ROSIDL_GENERATOR_C_PUBLIC_aic_engine_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
  rosidl_typesupport_c,
  aic_engine_interfaces,
  srv,
  ResetJoints_Response
)(void);

// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"

// Forward declare the get type support functions for this type.
ROSIDL_GENERATOR_C_PUBLIC_aic_engine_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
  rosidl_typesupport_c,
  aic_engine_interfaces,
  srv,
  ResetJoints_Event
)(void);

#include "rosidl_runtime_c/service_type_support_struct.h"

// Forward declare the get type support functions for this type.
ROSIDL_GENERATOR_C_PUBLIC_aic_engine_interfaces
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(
  rosidl_typesupport_c,
  aic_engine_interfaces,
  srv,
  ResetJoints
)(void);

// Forward declare the function to create a service event message for this type.
ROSIDL_GENERATOR_C_PUBLIC_aic_engine_interfaces
void *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_CREATE_EVENT_MESSAGE_SYMBOL_NAME(
  rosidl_typesupport_c,
  aic_engine_interfaces,
  srv,
  ResetJoints
)(
  const rosidl_service_introspection_info_t * info,
  rcutils_allocator_t * allocator,
  const void * request_message,
  const void * response_message);

// Forward declare the function to destroy a service event message for this type.
ROSIDL_GENERATOR_C_PUBLIC_aic_engine_interfaces
bool
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_DESTROY_EVENT_MESSAGE_SYMBOL_NAME(
  rosidl_typesupport_c,
  aic_engine_interfaces,
  srv,
  ResetJoints
)(
  void * event_msg,
  rcutils_allocator_t * allocator);

#ifdef __cplusplus
}
#endif

#endif  // AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__TYPE_SUPPORT_H_
