// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from aic_training_interfaces:srv/ExpandXacro.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "aic_training_interfaces/srv/expand_xacro.hpp"


#ifndef AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__BUILDER_HPP_
#define AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "aic_training_interfaces/srv/detail/expand_xacro__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace aic_training_interfaces
{

namespace srv
{

namespace builder
{

class Init_ExpandXacro_Request_xacro_arguments
{
public:
  explicit Init_ExpandXacro_Request_xacro_arguments(::aic_training_interfaces::srv::ExpandXacro_Request & msg)
  : msg_(msg)
  {}
  ::aic_training_interfaces::srv::ExpandXacro_Request xacro_arguments(::aic_training_interfaces::srv::ExpandXacro_Request::_xacro_arguments_type arg)
  {
    msg_.xacro_arguments = std::move(arg);
    return std::move(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Request msg_;
};

class Init_ExpandXacro_Request_relative_path
{
public:
  explicit Init_ExpandXacro_Request_relative_path(::aic_training_interfaces::srv::ExpandXacro_Request & msg)
  : msg_(msg)
  {}
  Init_ExpandXacro_Request_xacro_arguments relative_path(::aic_training_interfaces::srv::ExpandXacro_Request::_relative_path_type arg)
  {
    msg_.relative_path = std::move(arg);
    return Init_ExpandXacro_Request_xacro_arguments(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Request msg_;
};

class Init_ExpandXacro_Request_package_name
{
public:
  Init_ExpandXacro_Request_package_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExpandXacro_Request_relative_path package_name(::aic_training_interfaces::srv::ExpandXacro_Request::_package_name_type arg)
  {
    msg_.package_name = std::move(arg);
    return Init_ExpandXacro_Request_relative_path(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::aic_training_interfaces::srv::ExpandXacro_Request>()
{
  return aic_training_interfaces::srv::builder::Init_ExpandXacro_Request_package_name();
}

}  // namespace aic_training_interfaces


namespace aic_training_interfaces
{

namespace srv
{

namespace builder
{

class Init_ExpandXacro_Response_message
{
public:
  explicit Init_ExpandXacro_Response_message(::aic_training_interfaces::srv::ExpandXacro_Response & msg)
  : msg_(msg)
  {}
  ::aic_training_interfaces::srv::ExpandXacro_Response message(::aic_training_interfaces::srv::ExpandXacro_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Response msg_;
};

class Init_ExpandXacro_Response_xml
{
public:
  explicit Init_ExpandXacro_Response_xml(::aic_training_interfaces::srv::ExpandXacro_Response & msg)
  : msg_(msg)
  {}
  Init_ExpandXacro_Response_message xml(::aic_training_interfaces::srv::ExpandXacro_Response::_xml_type arg)
  {
    msg_.xml = std::move(arg);
    return Init_ExpandXacro_Response_message(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Response msg_;
};

class Init_ExpandXacro_Response_success
{
public:
  Init_ExpandXacro_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExpandXacro_Response_xml success(::aic_training_interfaces::srv::ExpandXacro_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_ExpandXacro_Response_xml(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::aic_training_interfaces::srv::ExpandXacro_Response>()
{
  return aic_training_interfaces::srv::builder::Init_ExpandXacro_Response_success();
}

}  // namespace aic_training_interfaces


namespace aic_training_interfaces
{

namespace srv
{

namespace builder
{

class Init_ExpandXacro_Event_response
{
public:
  explicit Init_ExpandXacro_Event_response(::aic_training_interfaces::srv::ExpandXacro_Event & msg)
  : msg_(msg)
  {}
  ::aic_training_interfaces::srv::ExpandXacro_Event response(::aic_training_interfaces::srv::ExpandXacro_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Event msg_;
};

class Init_ExpandXacro_Event_request
{
public:
  explicit Init_ExpandXacro_Event_request(::aic_training_interfaces::srv::ExpandXacro_Event & msg)
  : msg_(msg)
  {}
  Init_ExpandXacro_Event_response request(::aic_training_interfaces::srv::ExpandXacro_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_ExpandXacro_Event_response(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Event msg_;
};

class Init_ExpandXacro_Event_info
{
public:
  Init_ExpandXacro_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExpandXacro_Event_request info(::aic_training_interfaces::srv::ExpandXacro_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_ExpandXacro_Event_request(msg_);
  }

private:
  ::aic_training_interfaces::srv::ExpandXacro_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::aic_training_interfaces::srv::ExpandXacro_Event>()
{
  return aic_training_interfaces::srv::builder::Init_ExpandXacro_Event_info();
}

}  // namespace aic_training_interfaces

#endif  // AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__BUILDER_HPP_
