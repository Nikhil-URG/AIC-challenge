// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from aic_training_interfaces:srv/ExpandXacro.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "aic_training_interfaces/srv/detail/expand_xacro__functions.h"
#include "aic_training_interfaces/srv/detail/expand_xacro__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace aic_training_interfaces
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

void ExpandXacro_Request_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) aic_training_interfaces::srv::ExpandXacro_Request(_init);
}

void ExpandXacro_Request_fini_function(void * message_memory)
{
  auto typed_message = static_cast<aic_training_interfaces::srv::ExpandXacro_Request *>(message_memory);
  typed_message->~ExpandXacro_Request();
}

size_t size_function__ExpandXacro_Request__xacro_arguments(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ExpandXacro_Request__xacro_arguments(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void * get_function__ExpandXacro_Request__xacro_arguments(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void fetch_function__ExpandXacro_Request__xacro_arguments(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const std::string *>(
    get_const_function__ExpandXacro_Request__xacro_arguments(untyped_member, index));
  auto & value = *reinterpret_cast<std::string *>(untyped_value);
  value = item;
}

void assign_function__ExpandXacro_Request__xacro_arguments(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<std::string *>(
    get_function__ExpandXacro_Request__xacro_arguments(untyped_member, index));
  const auto & value = *reinterpret_cast<const std::string *>(untyped_value);
  item = value;
}

void resize_function__ExpandXacro_Request__xacro_arguments(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<std::string> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember ExpandXacro_Request_message_member_array[3] = {
  {
    "package_name",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Request, package_name),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "relative_path",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Request, relative_path),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "xacro_arguments",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Request, xacro_arguments),  // bytes offset in struct
    nullptr,  // default value
    size_function__ExpandXacro_Request__xacro_arguments,  // size() function pointer
    get_const_function__ExpandXacro_Request__xacro_arguments,  // get_const(index) function pointer
    get_function__ExpandXacro_Request__xacro_arguments,  // get(index) function pointer
    fetch_function__ExpandXacro_Request__xacro_arguments,  // fetch(index, &value) function pointer
    assign_function__ExpandXacro_Request__xacro_arguments,  // assign(index, value) function pointer
    resize_function__ExpandXacro_Request__xacro_arguments  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers ExpandXacro_Request_message_members = {
  "aic_training_interfaces::srv",  // message namespace
  "ExpandXacro_Request",  // message name
  3,  // number of fields
  sizeof(aic_training_interfaces::srv::ExpandXacro_Request),
  false,  // has_any_key_member_
  ExpandXacro_Request_message_member_array,  // message members
  ExpandXacro_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  ExpandXacro_Request_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t ExpandXacro_Request_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ExpandXacro_Request_message_members,
  get_message_typesupport_handle_function,
  &aic_training_interfaces__srv__ExpandXacro_Request__get_type_hash,
  &aic_training_interfaces__srv__ExpandXacro_Request__get_type_description,
  &aic_training_interfaces__srv__ExpandXacro_Request__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace aic_training_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<aic_training_interfaces::srv::ExpandXacro_Request>()
{
  return &::aic_training_interfaces::srv::rosidl_typesupport_introspection_cpp::ExpandXacro_Request_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, aic_training_interfaces, srv, ExpandXacro_Request)() {
  return &::aic_training_interfaces::srv::rosidl_typesupport_introspection_cpp::ExpandXacro_Request_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "array"
// already included above
// #include "cstddef"
// already included above
// #include "string"
// already included above
// #include "vector"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "aic_training_interfaces/srv/detail/expand_xacro__functions.h"
// already included above
// #include "aic_training_interfaces/srv/detail/expand_xacro__struct.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/field_types.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace aic_training_interfaces
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

void ExpandXacro_Response_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) aic_training_interfaces::srv::ExpandXacro_Response(_init);
}

void ExpandXacro_Response_fini_function(void * message_memory)
{
  auto typed_message = static_cast<aic_training_interfaces::srv::ExpandXacro_Response *>(message_memory);
  typed_message->~ExpandXacro_Response();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember ExpandXacro_Response_message_member_array[3] = {
  {
    "success",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Response, success),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "xml",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Response, xml),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "message",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Response, message),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers ExpandXacro_Response_message_members = {
  "aic_training_interfaces::srv",  // message namespace
  "ExpandXacro_Response",  // message name
  3,  // number of fields
  sizeof(aic_training_interfaces::srv::ExpandXacro_Response),
  false,  // has_any_key_member_
  ExpandXacro_Response_message_member_array,  // message members
  ExpandXacro_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  ExpandXacro_Response_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t ExpandXacro_Response_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ExpandXacro_Response_message_members,
  get_message_typesupport_handle_function,
  &aic_training_interfaces__srv__ExpandXacro_Response__get_type_hash,
  &aic_training_interfaces__srv__ExpandXacro_Response__get_type_description,
  &aic_training_interfaces__srv__ExpandXacro_Response__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace aic_training_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<aic_training_interfaces::srv::ExpandXacro_Response>()
{
  return &::aic_training_interfaces::srv::rosidl_typesupport_introspection_cpp::ExpandXacro_Response_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, aic_training_interfaces, srv, ExpandXacro_Response)() {
  return &::aic_training_interfaces::srv::rosidl_typesupport_introspection_cpp::ExpandXacro_Response_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "array"
// already included above
// #include "cstddef"
// already included above
// #include "string"
// already included above
// #include "vector"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "aic_training_interfaces/srv/detail/expand_xacro__functions.h"
// already included above
// #include "aic_training_interfaces/srv/detail/expand_xacro__struct.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/field_types.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace aic_training_interfaces
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

void ExpandXacro_Event_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) aic_training_interfaces::srv::ExpandXacro_Event(_init);
}

void ExpandXacro_Event_fini_function(void * message_memory)
{
  auto typed_message = static_cast<aic_training_interfaces::srv::ExpandXacro_Event *>(message_memory);
  typed_message->~ExpandXacro_Event();
}

size_t size_function__ExpandXacro_Event__request(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<aic_training_interfaces::srv::ExpandXacro_Request> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ExpandXacro_Event__request(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<aic_training_interfaces::srv::ExpandXacro_Request> *>(untyped_member);
  return &member[index];
}

void * get_function__ExpandXacro_Event__request(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<aic_training_interfaces::srv::ExpandXacro_Request> *>(untyped_member);
  return &member[index];
}

void fetch_function__ExpandXacro_Event__request(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const aic_training_interfaces::srv::ExpandXacro_Request *>(
    get_const_function__ExpandXacro_Event__request(untyped_member, index));
  auto & value = *reinterpret_cast<aic_training_interfaces::srv::ExpandXacro_Request *>(untyped_value);
  value = item;
}

void assign_function__ExpandXacro_Event__request(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<aic_training_interfaces::srv::ExpandXacro_Request *>(
    get_function__ExpandXacro_Event__request(untyped_member, index));
  const auto & value = *reinterpret_cast<const aic_training_interfaces::srv::ExpandXacro_Request *>(untyped_value);
  item = value;
}

void resize_function__ExpandXacro_Event__request(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<aic_training_interfaces::srv::ExpandXacro_Request> *>(untyped_member);
  member->resize(size);
}

size_t size_function__ExpandXacro_Event__response(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<aic_training_interfaces::srv::ExpandXacro_Response> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ExpandXacro_Event__response(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<aic_training_interfaces::srv::ExpandXacro_Response> *>(untyped_member);
  return &member[index];
}

void * get_function__ExpandXacro_Event__response(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<aic_training_interfaces::srv::ExpandXacro_Response> *>(untyped_member);
  return &member[index];
}

void fetch_function__ExpandXacro_Event__response(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const aic_training_interfaces::srv::ExpandXacro_Response *>(
    get_const_function__ExpandXacro_Event__response(untyped_member, index));
  auto & value = *reinterpret_cast<aic_training_interfaces::srv::ExpandXacro_Response *>(untyped_value);
  value = item;
}

void assign_function__ExpandXacro_Event__response(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<aic_training_interfaces::srv::ExpandXacro_Response *>(
    get_function__ExpandXacro_Event__response(untyped_member, index));
  const auto & value = *reinterpret_cast<const aic_training_interfaces::srv::ExpandXacro_Response *>(untyped_value);
  item = value;
}

void resize_function__ExpandXacro_Event__response(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<aic_training_interfaces::srv::ExpandXacro_Response> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember ExpandXacro_Event_message_member_array[3] = {
  {
    "info",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<service_msgs::msg::ServiceEventInfo>(),  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Event, info),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "request",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<aic_training_interfaces::srv::ExpandXacro_Request>(),  // members of sub message
    false,  // is key
    true,  // is array
    1,  // array size
    true,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Event, request),  // bytes offset in struct
    nullptr,  // default value
    size_function__ExpandXacro_Event__request,  // size() function pointer
    get_const_function__ExpandXacro_Event__request,  // get_const(index) function pointer
    get_function__ExpandXacro_Event__request,  // get(index) function pointer
    fetch_function__ExpandXacro_Event__request,  // fetch(index, &value) function pointer
    assign_function__ExpandXacro_Event__request,  // assign(index, value) function pointer
    resize_function__ExpandXacro_Event__request  // resize(index) function pointer
  },
  {
    "response",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<aic_training_interfaces::srv::ExpandXacro_Response>(),  // members of sub message
    false,  // is key
    true,  // is array
    1,  // array size
    true,  // is upper bound
    offsetof(aic_training_interfaces::srv::ExpandXacro_Event, response),  // bytes offset in struct
    nullptr,  // default value
    size_function__ExpandXacro_Event__response,  // size() function pointer
    get_const_function__ExpandXacro_Event__response,  // get_const(index) function pointer
    get_function__ExpandXacro_Event__response,  // get(index) function pointer
    fetch_function__ExpandXacro_Event__response,  // fetch(index, &value) function pointer
    assign_function__ExpandXacro_Event__response,  // assign(index, value) function pointer
    resize_function__ExpandXacro_Event__response  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers ExpandXacro_Event_message_members = {
  "aic_training_interfaces::srv",  // message namespace
  "ExpandXacro_Event",  // message name
  3,  // number of fields
  sizeof(aic_training_interfaces::srv::ExpandXacro_Event),
  false,  // has_any_key_member_
  ExpandXacro_Event_message_member_array,  // message members
  ExpandXacro_Event_init_function,  // function to initialize message memory (memory has to be allocated)
  ExpandXacro_Event_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t ExpandXacro_Event_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ExpandXacro_Event_message_members,
  get_message_typesupport_handle_function,
  &aic_training_interfaces__srv__ExpandXacro_Event__get_type_hash,
  &aic_training_interfaces__srv__ExpandXacro_Event__get_type_description,
  &aic_training_interfaces__srv__ExpandXacro_Event__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace aic_training_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<aic_training_interfaces::srv::ExpandXacro_Event>()
{
  return &::aic_training_interfaces::srv::rosidl_typesupport_introspection_cpp::ExpandXacro_Event_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, aic_training_interfaces, srv, ExpandXacro_Event)() {
  return &::aic_training_interfaces::srv::rosidl_typesupport_introspection_cpp::ExpandXacro_Event_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_cpp/service_type_support.hpp"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "rosidl_typesupport_introspection_cpp/visibility_control.h"
// already included above
// #include "aic_training_interfaces/srv/detail/expand_xacro__functions.h"
// already included above
// #include "aic_training_interfaces/srv/detail/expand_xacro__struct.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/service_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/service_type_support_decl.hpp"

namespace aic_training_interfaces
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

// this is intentionally not const to allow initialization later to prevent an initialization race
static ::rosidl_typesupport_introspection_cpp::ServiceMembers ExpandXacro_service_members = {
  "aic_training_interfaces::srv",  // service namespace
  "ExpandXacro",  // service name
  // the following fields are initialized below on first access
  // see get_service_type_support_handle<aic_training_interfaces::srv::ExpandXacro>()
  nullptr,  // request message
  nullptr,  // response message
  nullptr,  // event message
};

static const rosidl_service_type_support_t ExpandXacro_service_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ExpandXacro_service_members,
  get_service_typesupport_handle_function,
  ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<aic_training_interfaces::srv::ExpandXacro_Request>(),
  ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<aic_training_interfaces::srv::ExpandXacro_Response>(),
  ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<aic_training_interfaces::srv::ExpandXacro_Event>(),
  &::rosidl_typesupport_cpp::service_create_event_message<aic_training_interfaces::srv::ExpandXacro>,
  &::rosidl_typesupport_cpp::service_destroy_event_message<aic_training_interfaces::srv::ExpandXacro>,
  &aic_training_interfaces__srv__ExpandXacro__get_type_hash,
  &aic_training_interfaces__srv__ExpandXacro__get_type_description,
  &aic_training_interfaces__srv__ExpandXacro__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace aic_training_interfaces


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_service_type_support_t *
get_service_type_support_handle<aic_training_interfaces::srv::ExpandXacro>()
{
  // get a handle to the value to be returned
  auto service_type_support =
    &::aic_training_interfaces::srv::rosidl_typesupport_introspection_cpp::ExpandXacro_service_type_support_handle;
  // get a non-const and properly typed version of the data void *
  auto service_members = const_cast<::rosidl_typesupport_introspection_cpp::ServiceMembers *>(
    static_cast<const ::rosidl_typesupport_introspection_cpp::ServiceMembers *>(
      service_type_support->data));
  // make sure all of the service_members are initialized
  // if they are not, initialize them
  if (
    service_members->request_members_ == nullptr ||
    service_members->response_members_ == nullptr ||
    service_members->event_members_ == nullptr)
  {
    // initialize the request_members_ with the static function from the external library
    service_members->request_members_ = static_cast<
      const ::rosidl_typesupport_introspection_cpp::MessageMembers *
      >(
      ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
        ::aic_training_interfaces::srv::ExpandXacro_Request
      >()->data
      );
    // initialize the response_members_ with the static function from the external library
    service_members->response_members_ = static_cast<
      const ::rosidl_typesupport_introspection_cpp::MessageMembers *
      >(
      ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
        ::aic_training_interfaces::srv::ExpandXacro_Response
      >()->data
      );
    // initialize the event_members_ with the static function from the external library
    service_members->event_members_ = static_cast<
      const ::rosidl_typesupport_introspection_cpp::MessageMembers *
      >(
      ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
        ::aic_training_interfaces::srv::ExpandXacro_Event
      >()->data
      );
  }
  // finally return the properly initialized service_type_support handle
  return service_type_support;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, aic_training_interfaces, srv, ExpandXacro)() {
  return ::rosidl_typesupport_introspection_cpp::get_service_type_support_handle<aic_training_interfaces::srv::ExpandXacro>();
}

#ifdef __cplusplus
}
#endif
