// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from aic_engine_interfaces:srv/ResetJoints.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "aic_engine_interfaces/srv/reset_joints.hpp"


#ifndef AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__TRAITS_HPP_
#define AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "aic_engine_interfaces/srv/detail/reset_joints__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace aic_engine_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const ResetJoints_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: joint_names
  {
    if (msg.joint_names.size() == 0) {
      out << "joint_names: []";
    } else {
      out << "joint_names: [";
      size_t pending_items = msg.joint_names.size();
      for (auto item : msg.joint_names) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: initial_positions
  {
    if (msg.initial_positions.size() == 0) {
      out << "initial_positions: []";
    } else {
      out << "initial_positions: [";
      size_t pending_items = msg.initial_positions.size();
      for (auto item : msg.initial_positions) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ResetJoints_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: joint_names
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.joint_names.size() == 0) {
      out << "joint_names: []\n";
    } else {
      out << "joint_names:\n";
      for (auto item : msg.joint_names) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: initial_positions
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.initial_positions.size() == 0) {
      out << "initial_positions: []\n";
    } else {
      out << "initial_positions:\n";
      for (auto item : msg.initial_positions) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ResetJoints_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace aic_engine_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use aic_engine_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const aic_engine_interfaces::srv::ResetJoints_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  aic_engine_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use aic_engine_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const aic_engine_interfaces::srv::ResetJoints_Request & msg)
{
  return aic_engine_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<aic_engine_interfaces::srv::ResetJoints_Request>()
{
  return "aic_engine_interfaces::srv::ResetJoints_Request";
}

template<>
inline const char * name<aic_engine_interfaces::srv::ResetJoints_Request>()
{
  return "aic_engine_interfaces/srv/ResetJoints_Request";
}

template<>
struct has_fixed_size<aic_engine_interfaces::srv::ResetJoints_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<aic_engine_interfaces::srv::ResetJoints_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<aic_engine_interfaces::srv::ResetJoints_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace aic_engine_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const ResetJoints_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ResetJoints_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ResetJoints_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace aic_engine_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use aic_engine_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const aic_engine_interfaces::srv::ResetJoints_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  aic_engine_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use aic_engine_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const aic_engine_interfaces::srv::ResetJoints_Response & msg)
{
  return aic_engine_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<aic_engine_interfaces::srv::ResetJoints_Response>()
{
  return "aic_engine_interfaces::srv::ResetJoints_Response";
}

template<>
inline const char * name<aic_engine_interfaces::srv::ResetJoints_Response>()
{
  return "aic_engine_interfaces/srv/ResetJoints_Response";
}

template<>
struct has_fixed_size<aic_engine_interfaces::srv::ResetJoints_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<aic_engine_interfaces::srv::ResetJoints_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<aic_engine_interfaces::srv::ResetJoints_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__traits.hpp"

namespace aic_engine_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const ResetJoints_Event & msg,
  std::ostream & out)
{
  out << "{";
  // member: info
  {
    out << "info: ";
    to_flow_style_yaml(msg.info, out);
    out << ", ";
  }

  // member: request
  {
    if (msg.request.size() == 0) {
      out << "request: []";
    } else {
      out << "request: [";
      size_t pending_items = msg.request.size();
      for (auto item : msg.request) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: response
  {
    if (msg.response.size() == 0) {
      out << "response: []";
    } else {
      out << "response: [";
      size_t pending_items = msg.response.size();
      for (auto item : msg.response) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ResetJoints_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: info
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "info:\n";
    to_block_style_yaml(msg.info, out, indentation + 2);
  }

  // member: request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.request.size() == 0) {
      out << "request: []\n";
    } else {
      out << "request:\n";
      for (auto item : msg.request) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: response
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.response.size() == 0) {
      out << "response: []\n";
    } else {
      out << "response:\n";
      for (auto item : msg.response) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ResetJoints_Event & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace aic_engine_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use aic_engine_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const aic_engine_interfaces::srv::ResetJoints_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  aic_engine_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use aic_engine_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const aic_engine_interfaces::srv::ResetJoints_Event & msg)
{
  return aic_engine_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<aic_engine_interfaces::srv::ResetJoints_Event>()
{
  return "aic_engine_interfaces::srv::ResetJoints_Event";
}

template<>
inline const char * name<aic_engine_interfaces::srv::ResetJoints_Event>()
{
  return "aic_engine_interfaces/srv/ResetJoints_Event";
}

template<>
struct has_fixed_size<aic_engine_interfaces::srv::ResetJoints_Event>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<aic_engine_interfaces::srv::ResetJoints_Event>
  : std::integral_constant<bool, has_bounded_size<aic_engine_interfaces::srv::ResetJoints_Request>::value && has_bounded_size<aic_engine_interfaces::srv::ResetJoints_Response>::value && has_bounded_size<service_msgs::msg::ServiceEventInfo>::value> {};

template<>
struct is_message<aic_engine_interfaces::srv::ResetJoints_Event>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<aic_engine_interfaces::srv::ResetJoints>()
{
  return "aic_engine_interfaces::srv::ResetJoints";
}

template<>
inline const char * name<aic_engine_interfaces::srv::ResetJoints>()
{
  return "aic_engine_interfaces/srv/ResetJoints";
}

template<>
struct has_fixed_size<aic_engine_interfaces::srv::ResetJoints>
  : std::integral_constant<
    bool,
    has_fixed_size<aic_engine_interfaces::srv::ResetJoints_Request>::value &&
    has_fixed_size<aic_engine_interfaces::srv::ResetJoints_Response>::value
  >
{
};

template<>
struct has_bounded_size<aic_engine_interfaces::srv::ResetJoints>
  : std::integral_constant<
    bool,
    has_bounded_size<aic_engine_interfaces::srv::ResetJoints_Request>::value &&
    has_bounded_size<aic_engine_interfaces::srv::ResetJoints_Response>::value
  >
{
};

template<>
struct is_service<aic_engine_interfaces::srv::ResetJoints>
  : std::true_type
{
};

template<>
struct is_service_request<aic_engine_interfaces::srv::ResetJoints_Request>
  : std::true_type
{
};

template<>
struct is_service_response<aic_engine_interfaces::srv::ResetJoints_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__TRAITS_HPP_
