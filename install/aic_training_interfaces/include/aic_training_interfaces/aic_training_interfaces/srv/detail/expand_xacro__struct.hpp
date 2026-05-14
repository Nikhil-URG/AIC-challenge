// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from aic_training_interfaces:srv/ExpandXacro.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "aic_training_interfaces/srv/expand_xacro.hpp"


#ifndef AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__STRUCT_HPP_
#define AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Request __attribute__((deprecated))
#else
# define DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Request __declspec(deprecated)
#endif

namespace aic_training_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ExpandXacro_Request_
{
  using Type = ExpandXacro_Request_<ContainerAllocator>;

  explicit ExpandXacro_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->package_name = "";
      this->relative_path = "";
    }
  }

  explicit ExpandXacro_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : package_name(_alloc),
    relative_path(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->package_name = "";
      this->relative_path = "";
    }
  }

  // field types and members
  using _package_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _package_name_type package_name;
  using _relative_path_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _relative_path_type relative_path;
  using _xacro_arguments_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _xacro_arguments_type xacro_arguments;

  // setters for named parameter idiom
  Type & set__package_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->package_name = _arg;
    return *this;
  }
  Type & set__relative_path(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->relative_path = _arg;
    return *this;
  }
  Type & set__xacro_arguments(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->xacro_arguments = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Request
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Request
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExpandXacro_Request_ & other) const
  {
    if (this->package_name != other.package_name) {
      return false;
    }
    if (this->relative_path != other.relative_path) {
      return false;
    }
    if (this->xacro_arguments != other.xacro_arguments) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExpandXacro_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExpandXacro_Request_

// alias to use template instance with default allocator
using ExpandXacro_Request =
  aic_training_interfaces::srv::ExpandXacro_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace aic_training_interfaces


#ifndef _WIN32
# define DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Response __attribute__((deprecated))
#else
# define DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Response __declspec(deprecated)
#endif

namespace aic_training_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ExpandXacro_Response_
{
  using Type = ExpandXacro_Response_<ContainerAllocator>;

  explicit ExpandXacro_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->xml = "";
      this->message = "";
    }
  }

  explicit ExpandXacro_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : xml(_alloc),
    message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->xml = "";
      this->message = "";
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _xml_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _xml_type xml;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__xml(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->xml = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Response
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Response
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExpandXacro_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->xml != other.xml) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExpandXacro_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExpandXacro_Response_

// alias to use template instance with default allocator
using ExpandXacro_Response =
  aic_training_interfaces::srv::ExpandXacro_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace aic_training_interfaces


// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Event __attribute__((deprecated))
#else
# define DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Event __declspec(deprecated)
#endif

namespace aic_training_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ExpandXacro_Event_
{
  using Type = ExpandXacro_Event_<ContainerAllocator>;

  explicit ExpandXacro_Event_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_init)
  {
    (void)_init;
  }

  explicit ExpandXacro_Event_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _info_type =
    service_msgs::msg::ServiceEventInfo_<ContainerAllocator>;
  _info_type info;
  using _request_type =
    rosidl_runtime_cpp::BoundedVector<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>>>;
  _request_type request;
  using _response_type =
    rosidl_runtime_cpp::BoundedVector<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>>>;
  _response_type response;

  // setters for named parameter idiom
  Type & set__info(
    const service_msgs::msg::ServiceEventInfo_<ContainerAllocator> & _arg)
  {
    this->info = _arg;
    return *this;
  }
  Type & set__request(
    const rosidl_runtime_cpp::BoundedVector<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<aic_training_interfaces::srv::ExpandXacro_Request_<ContainerAllocator>>> & _arg)
  {
    this->request = _arg;
    return *this;
  }
  Type & set__response(
    const rosidl_runtime_cpp::BoundedVector<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<aic_training_interfaces::srv::ExpandXacro_Response_<ContainerAllocator>>> & _arg)
  {
    this->response = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator> *;
  using ConstRawPtr =
    const aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Event
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__aic_training_interfaces__srv__ExpandXacro_Event
    std::shared_ptr<aic_training_interfaces::srv::ExpandXacro_Event_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExpandXacro_Event_ & other) const
  {
    if (this->info != other.info) {
      return false;
    }
    if (this->request != other.request) {
      return false;
    }
    if (this->response != other.response) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExpandXacro_Event_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExpandXacro_Event_

// alias to use template instance with default allocator
using ExpandXacro_Event =
  aic_training_interfaces::srv::ExpandXacro_Event_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace aic_training_interfaces

namespace aic_training_interfaces
{

namespace srv
{

struct ExpandXacro
{
  using Request = aic_training_interfaces::srv::ExpandXacro_Request;
  using Response = aic_training_interfaces::srv::ExpandXacro_Response;
  using Event = aic_training_interfaces::srv::ExpandXacro_Event;
};

}  // namespace srv

}  // namespace aic_training_interfaces

#endif  // AIC_TRAINING_INTERFACES__SRV__DETAIL__EXPAND_XACRO__STRUCT_HPP_
