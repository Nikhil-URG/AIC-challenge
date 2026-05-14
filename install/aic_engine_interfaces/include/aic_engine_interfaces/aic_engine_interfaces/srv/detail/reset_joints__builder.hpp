// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from aic_engine_interfaces:srv/ResetJoints.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "aic_engine_interfaces/srv/reset_joints.hpp"


#ifndef AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__BUILDER_HPP_
#define AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "aic_engine_interfaces/srv/detail/reset_joints__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace aic_engine_interfaces
{

namespace srv
{

namespace builder
{

class Init_ResetJoints_Request_initial_positions
{
public:
  explicit Init_ResetJoints_Request_initial_positions(::aic_engine_interfaces::srv::ResetJoints_Request & msg)
  : msg_(msg)
  {}
  ::aic_engine_interfaces::srv::ResetJoints_Request initial_positions(::aic_engine_interfaces::srv::ResetJoints_Request::_initial_positions_type arg)
  {
    msg_.initial_positions = std::move(arg);
    return std::move(msg_);
  }

private:
  ::aic_engine_interfaces::srv::ResetJoints_Request msg_;
};

class Init_ResetJoints_Request_joint_names
{
public:
  Init_ResetJoints_Request_joint_names()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ResetJoints_Request_initial_positions joint_names(::aic_engine_interfaces::srv::ResetJoints_Request::_joint_names_type arg)
  {
    msg_.joint_names = std::move(arg);
    return Init_ResetJoints_Request_initial_positions(msg_);
  }

private:
  ::aic_engine_interfaces::srv::ResetJoints_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::aic_engine_interfaces::srv::ResetJoints_Request>()
{
  return aic_engine_interfaces::srv::builder::Init_ResetJoints_Request_joint_names();
}

}  // namespace aic_engine_interfaces


namespace aic_engine_interfaces
{

namespace srv
{

namespace builder
{

class Init_ResetJoints_Response_message
{
public:
  explicit Init_ResetJoints_Response_message(::aic_engine_interfaces::srv::ResetJoints_Response & msg)
  : msg_(msg)
  {}
  ::aic_engine_interfaces::srv::ResetJoints_Response message(::aic_engine_interfaces::srv::ResetJoints_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::aic_engine_interfaces::srv::ResetJoints_Response msg_;
};

class Init_ResetJoints_Response_success
{
public:
  Init_ResetJoints_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ResetJoints_Response_message success(::aic_engine_interfaces::srv::ResetJoints_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_ResetJoints_Response_message(msg_);
  }

private:
  ::aic_engine_interfaces::srv::ResetJoints_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::aic_engine_interfaces::srv::ResetJoints_Response>()
{
  return aic_engine_interfaces::srv::builder::Init_ResetJoints_Response_success();
}

}  // namespace aic_engine_interfaces


namespace aic_engine_interfaces
{

namespace srv
{

namespace builder
{

class Init_ResetJoints_Event_response
{
public:
  explicit Init_ResetJoints_Event_response(::aic_engine_interfaces::srv::ResetJoints_Event & msg)
  : msg_(msg)
  {}
  ::aic_engine_interfaces::srv::ResetJoints_Event response(::aic_engine_interfaces::srv::ResetJoints_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::aic_engine_interfaces::srv::ResetJoints_Event msg_;
};

class Init_ResetJoints_Event_request
{
public:
  explicit Init_ResetJoints_Event_request(::aic_engine_interfaces::srv::ResetJoints_Event & msg)
  : msg_(msg)
  {}
  Init_ResetJoints_Event_response request(::aic_engine_interfaces::srv::ResetJoints_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_ResetJoints_Event_response(msg_);
  }

private:
  ::aic_engine_interfaces::srv::ResetJoints_Event msg_;
};

class Init_ResetJoints_Event_info
{
public:
  Init_ResetJoints_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ResetJoints_Event_request info(::aic_engine_interfaces::srv::ResetJoints_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_ResetJoints_Event_request(msg_);
  }

private:
  ::aic_engine_interfaces::srv::ResetJoints_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::aic_engine_interfaces::srv::ResetJoints_Event>()
{
  return aic_engine_interfaces::srv::builder::Init_ResetJoints_Event_info();
}

}  // namespace aic_engine_interfaces

#endif  // AIC_ENGINE_INTERFACES__SRV__DETAIL__RESET_JOINTS__BUILDER_HPP_
