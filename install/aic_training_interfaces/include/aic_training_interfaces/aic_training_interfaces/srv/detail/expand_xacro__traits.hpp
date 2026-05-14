// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from aic_training_interfaces:srv/ExpandXacro.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "aic_training_interfaces/srv/expand_xacro.hpp"


#ifndef AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__TRAITS_HPP_
#define AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "aic_training_interfaces/srv/detail/expand_xacro__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace aic_training_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const ExpandXacro_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: package_name
  {
    out << "package_name: ";
    rosidl_generator_traits::value_to_yaml(msg.package_name, out);
    out << ", ";
  }

  // member: relative_path
  {
    out << "relative_path: ";
    rosidl_generator_traits::value_to_yaml(msg.relative_path, out);
    out << ", ";
  }

  // member: xacro_arguments
  {
    if (msg.xacro_arguments.size() == 0) {
      out << "xacro_arguments: []";
    } else {
      out << "xacro_arguments: [";
      size_t pending_items = msg.xacro_arguments.size();
      for (auto item : msg.xacro_arguments) {
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
  const ExpandXacro_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: package_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "package_name: ";
    rosidl_generator_traits::value_to_yaml(msg.package_name, out);
    out << "\n";
  }

  // member: relative_path
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "relative_path: ";
    rosidl_generator_traits::value_to_yaml(msg.relative_path, out);
    out << "\n";
  }

  // member: xacro_arguments
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.xacro_arguments.size() == 0) {
      out << "xacro_arguments: []\n";
    } else {
      out << "xacro_arguments:\n";
      for (auto item : msg.xacro_arguments) {
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

inline std::string to_yaml(const ExpandXacro_Request & msg, bool use_flow_style = false)
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

}  // namespace aic_training_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use aic_training_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const aic_training_interfaces::srv::ExpandXacro_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  aic_training_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use aic_training_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const aic_training_interfaces::srv::ExpandXacro_Request & msg)
{
  return aic_training_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<aic_training_interfaces::srv::ExpandXacro_Request>()
{
  return "aic_training_interfaces::srv::ExpandXacro_Request";
}

template<>
inline const char * name<aic_training_interfaces::srv::ExpandXacro_Request>()
{
  return "aic_training_interfaces/srv/ExpandXacro_Request";
}

template<>
struct has_fixed_size<aic_training_interfaces::srv::ExpandXacro_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<aic_training_interfaces::srv::ExpandXacro_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<aic_training_interfaces::srv::ExpandXacro_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace aic_training_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const ExpandXacro_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: xml
  {
    out << "xml: ";
    rosidl_generator_traits::value_to_yaml(msg.xml, out);
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
  const ExpandXacro_Response & msg,
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

  // member: xml
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "xml: ";
    rosidl_generator_traits::value_to_yaml(msg.xml, out);
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

inline std::string to_yaml(const ExpandXacro_Response & msg, bool use_flow_style = false)
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

}  // namespace aic_training_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use aic_training_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const aic_training_interfaces::srv::ExpandXacro_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  aic_training_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use aic_training_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const aic_training_interfaces::srv::ExpandXacro_Response & msg)
{
  return aic_training_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<aic_training_interfaces::srv::ExpandXacro_Response>()
{
  return "aic_training_interfaces::srv::ExpandXacro_Response";
}

template<>
inline const char * name<aic_training_interfaces::srv::ExpandXacro_Response>()
{
  return "aic_training_interfaces/srv/ExpandXacro_Response";
}

template<>
struct has_fixed_size<aic_training_interfaces::srv::ExpandXacro_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<aic_training_interfaces::srv::ExpandXacro_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<aic_training_interfaces::srv::ExpandXacro_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__traits.hpp"

namespace aic_training_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const ExpandXacro_Event & msg,
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
  const ExpandXacro_Event & msg,
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

inline std::string to_yaml(const ExpandXacro_Event & msg, bool use_flow_style = false)
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

}  // namespace aic_training_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use aic_training_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const aic_training_interfaces::srv::ExpandXacro_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  aic_training_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use aic_training_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const aic_training_interfaces::srv::ExpandXacro_Event & msg)
{
  return aic_training_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<aic_training_interfaces::srv::ExpandXacro_Event>()
{
  return "aic_training_interfaces::srv::ExpandXacro_Event";
}

template<>
inline const char * name<aic_training_interfaces::srv::ExpandXacro_Event>()
{
  return "aic_training_interfaces/srv/ExpandXacro_Event";
}

template<>
struct has_fixed_size<aic_training_interfaces::srv::ExpandXacro_Event>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<aic_training_interfaces::srv::ExpandXacro_Event>
  : std::integral_constant<bool, has_bounded_size<aic_training_interfaces::srv::ExpandXacro_Request>::value && has_bounded_size<aic_training_interfaces::srv::ExpandXacro_Response>::value && has_bounded_size<service_msgs::msg::ServiceEventInfo>::value> {};

template<>
struct is_message<aic_training_interfaces::srv::ExpandXacro_Event>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<aic_training_interfaces::srv::ExpandXacro>()
{
  return "aic_training_interfaces::srv::ExpandXacro";
}

template<>
inline const char * name<aic_training_interfaces::srv::ExpandXacro>()
{
  return "aic_training_interfaces/srv/ExpandXacro";
}

template<>
struct has_fixed_size<aic_training_interfaces::srv::ExpandXacro>
  : std::integral_constant<
    bool,
    has_fixed_size<aic_training_interfaces::srv::ExpandXacro_Request>::value &&
    has_fixed_size<aic_training_interfaces::srv::ExpandXacro_Response>::value
  >
{
};

template<>
struct has_bounded_size<aic_training_interfaces::srv::ExpandXacro>
  : std::integral_constant<
    bool,
    has_bounded_size<aic_training_interfaces::srv::ExpandXacro_Request>::value &&
    has_bounded_size<aic_training_interfaces::srv::ExpandXacro_Response>::value
  >
{
};

template<>
struct is_service<aic_training_interfaces::srv::ExpandXacro>
  : std::true_type
{
};

template<>
struct is_service_request<aic_training_interfaces::srv::ExpandXacro_Request>
  : std::true_type
{
};

template<>
struct is_service_response<aic_training_interfaces::srv::ExpandXacro_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__TRAITS_HPP_
