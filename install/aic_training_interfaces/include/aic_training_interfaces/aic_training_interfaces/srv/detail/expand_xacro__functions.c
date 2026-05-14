// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from aic_training_interfaces:srv/ExpandXacro.idl
// generated code does not contain a copyright notice
#include "aic_training_interfaces/srv/detail/expand_xacro__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `package_name`
// Member `relative_path`
// Member `xacro_arguments`
#include "rosidl_runtime_c/string_functions.h"

bool
aic_training_interfaces__srv__ExpandXacro_Request__init(aic_training_interfaces__srv__ExpandXacro_Request * msg)
{
  if (!msg) {
    return false;
  }
  // package_name
  if (!rosidl_runtime_c__String__init(&msg->package_name)) {
    aic_training_interfaces__srv__ExpandXacro_Request__fini(msg);
    return false;
  }
  // relative_path
  if (!rosidl_runtime_c__String__init(&msg->relative_path)) {
    aic_training_interfaces__srv__ExpandXacro_Request__fini(msg);
    return false;
  }
  // xacro_arguments
  if (!rosidl_runtime_c__String__Sequence__init(&msg->xacro_arguments, 0)) {
    aic_training_interfaces__srv__ExpandXacro_Request__fini(msg);
    return false;
  }
  return true;
}

void
aic_training_interfaces__srv__ExpandXacro_Request__fini(aic_training_interfaces__srv__ExpandXacro_Request * msg)
{
  if (!msg) {
    return;
  }
  // package_name
  rosidl_runtime_c__String__fini(&msg->package_name);
  // relative_path
  rosidl_runtime_c__String__fini(&msg->relative_path);
  // xacro_arguments
  rosidl_runtime_c__String__Sequence__fini(&msg->xacro_arguments);
}

bool
aic_training_interfaces__srv__ExpandXacro_Request__are_equal(const aic_training_interfaces__srv__ExpandXacro_Request * lhs, const aic_training_interfaces__srv__ExpandXacro_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // package_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->package_name), &(rhs->package_name)))
  {
    return false;
  }
  // relative_path
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->relative_path), &(rhs->relative_path)))
  {
    return false;
  }
  // xacro_arguments
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->xacro_arguments), &(rhs->xacro_arguments)))
  {
    return false;
  }
  return true;
}

bool
aic_training_interfaces__srv__ExpandXacro_Request__copy(
  const aic_training_interfaces__srv__ExpandXacro_Request * input,
  aic_training_interfaces__srv__ExpandXacro_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // package_name
  if (!rosidl_runtime_c__String__copy(
      &(input->package_name), &(output->package_name)))
  {
    return false;
  }
  // relative_path
  if (!rosidl_runtime_c__String__copy(
      &(input->relative_path), &(output->relative_path)))
  {
    return false;
  }
  // xacro_arguments
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->xacro_arguments), &(output->xacro_arguments)))
  {
    return false;
  }
  return true;
}

aic_training_interfaces__srv__ExpandXacro_Request *
aic_training_interfaces__srv__ExpandXacro_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Request * msg = (aic_training_interfaces__srv__ExpandXacro_Request *)allocator.allocate(sizeof(aic_training_interfaces__srv__ExpandXacro_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(aic_training_interfaces__srv__ExpandXacro_Request));
  bool success = aic_training_interfaces__srv__ExpandXacro_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
aic_training_interfaces__srv__ExpandXacro_Request__destroy(aic_training_interfaces__srv__ExpandXacro_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    aic_training_interfaces__srv__ExpandXacro_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
aic_training_interfaces__srv__ExpandXacro_Request__Sequence__init(aic_training_interfaces__srv__ExpandXacro_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Request * data = NULL;

  if (size) {
    data = (aic_training_interfaces__srv__ExpandXacro_Request *)allocator.zero_allocate(size, sizeof(aic_training_interfaces__srv__ExpandXacro_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = aic_training_interfaces__srv__ExpandXacro_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        aic_training_interfaces__srv__ExpandXacro_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
aic_training_interfaces__srv__ExpandXacro_Request__Sequence__fini(aic_training_interfaces__srv__ExpandXacro_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      aic_training_interfaces__srv__ExpandXacro_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

aic_training_interfaces__srv__ExpandXacro_Request__Sequence *
aic_training_interfaces__srv__ExpandXacro_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Request__Sequence * array = (aic_training_interfaces__srv__ExpandXacro_Request__Sequence *)allocator.allocate(sizeof(aic_training_interfaces__srv__ExpandXacro_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = aic_training_interfaces__srv__ExpandXacro_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
aic_training_interfaces__srv__ExpandXacro_Request__Sequence__destroy(aic_training_interfaces__srv__ExpandXacro_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    aic_training_interfaces__srv__ExpandXacro_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
aic_training_interfaces__srv__ExpandXacro_Request__Sequence__are_equal(const aic_training_interfaces__srv__ExpandXacro_Request__Sequence * lhs, const aic_training_interfaces__srv__ExpandXacro_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!aic_training_interfaces__srv__ExpandXacro_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
aic_training_interfaces__srv__ExpandXacro_Request__Sequence__copy(
  const aic_training_interfaces__srv__ExpandXacro_Request__Sequence * input,
  aic_training_interfaces__srv__ExpandXacro_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(aic_training_interfaces__srv__ExpandXacro_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    aic_training_interfaces__srv__ExpandXacro_Request * data =
      (aic_training_interfaces__srv__ExpandXacro_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!aic_training_interfaces__srv__ExpandXacro_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          aic_training_interfaces__srv__ExpandXacro_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!aic_training_interfaces__srv__ExpandXacro_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `xml`
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
aic_training_interfaces__srv__ExpandXacro_Response__init(aic_training_interfaces__srv__ExpandXacro_Response * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // xml
  if (!rosidl_runtime_c__String__init(&msg->xml)) {
    aic_training_interfaces__srv__ExpandXacro_Response__fini(msg);
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    aic_training_interfaces__srv__ExpandXacro_Response__fini(msg);
    return false;
  }
  return true;
}

void
aic_training_interfaces__srv__ExpandXacro_Response__fini(aic_training_interfaces__srv__ExpandXacro_Response * msg)
{
  if (!msg) {
    return;
  }
  // success
  // xml
  rosidl_runtime_c__String__fini(&msg->xml);
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
aic_training_interfaces__srv__ExpandXacro_Response__are_equal(const aic_training_interfaces__srv__ExpandXacro_Response * lhs, const aic_training_interfaces__srv__ExpandXacro_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // xml
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->xml), &(rhs->xml)))
  {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
aic_training_interfaces__srv__ExpandXacro_Response__copy(
  const aic_training_interfaces__srv__ExpandXacro_Response * input,
  aic_training_interfaces__srv__ExpandXacro_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // xml
  if (!rosidl_runtime_c__String__copy(
      &(input->xml), &(output->xml)))
  {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

aic_training_interfaces__srv__ExpandXacro_Response *
aic_training_interfaces__srv__ExpandXacro_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Response * msg = (aic_training_interfaces__srv__ExpandXacro_Response *)allocator.allocate(sizeof(aic_training_interfaces__srv__ExpandXacro_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(aic_training_interfaces__srv__ExpandXacro_Response));
  bool success = aic_training_interfaces__srv__ExpandXacro_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
aic_training_interfaces__srv__ExpandXacro_Response__destroy(aic_training_interfaces__srv__ExpandXacro_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    aic_training_interfaces__srv__ExpandXacro_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
aic_training_interfaces__srv__ExpandXacro_Response__Sequence__init(aic_training_interfaces__srv__ExpandXacro_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Response * data = NULL;

  if (size) {
    data = (aic_training_interfaces__srv__ExpandXacro_Response *)allocator.zero_allocate(size, sizeof(aic_training_interfaces__srv__ExpandXacro_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = aic_training_interfaces__srv__ExpandXacro_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        aic_training_interfaces__srv__ExpandXacro_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
aic_training_interfaces__srv__ExpandXacro_Response__Sequence__fini(aic_training_interfaces__srv__ExpandXacro_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      aic_training_interfaces__srv__ExpandXacro_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

aic_training_interfaces__srv__ExpandXacro_Response__Sequence *
aic_training_interfaces__srv__ExpandXacro_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Response__Sequence * array = (aic_training_interfaces__srv__ExpandXacro_Response__Sequence *)allocator.allocate(sizeof(aic_training_interfaces__srv__ExpandXacro_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = aic_training_interfaces__srv__ExpandXacro_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
aic_training_interfaces__srv__ExpandXacro_Response__Sequence__destroy(aic_training_interfaces__srv__ExpandXacro_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    aic_training_interfaces__srv__ExpandXacro_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
aic_training_interfaces__srv__ExpandXacro_Response__Sequence__are_equal(const aic_training_interfaces__srv__ExpandXacro_Response__Sequence * lhs, const aic_training_interfaces__srv__ExpandXacro_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!aic_training_interfaces__srv__ExpandXacro_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
aic_training_interfaces__srv__ExpandXacro_Response__Sequence__copy(
  const aic_training_interfaces__srv__ExpandXacro_Response__Sequence * input,
  aic_training_interfaces__srv__ExpandXacro_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(aic_training_interfaces__srv__ExpandXacro_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    aic_training_interfaces__srv__ExpandXacro_Response * data =
      (aic_training_interfaces__srv__ExpandXacro_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!aic_training_interfaces__srv__ExpandXacro_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          aic_training_interfaces__srv__ExpandXacro_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!aic_training_interfaces__srv__ExpandXacro_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
#include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "aic_training_interfaces/srv/detail/expand_xacro__functions.h"

bool
aic_training_interfaces__srv__ExpandXacro_Event__init(aic_training_interfaces__srv__ExpandXacro_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    aic_training_interfaces__srv__ExpandXacro_Event__fini(msg);
    return false;
  }
  // request
  if (!aic_training_interfaces__srv__ExpandXacro_Request__Sequence__init(&msg->request, 0)) {
    aic_training_interfaces__srv__ExpandXacro_Event__fini(msg);
    return false;
  }
  // response
  if (!aic_training_interfaces__srv__ExpandXacro_Response__Sequence__init(&msg->response, 0)) {
    aic_training_interfaces__srv__ExpandXacro_Event__fini(msg);
    return false;
  }
  return true;
}

void
aic_training_interfaces__srv__ExpandXacro_Event__fini(aic_training_interfaces__srv__ExpandXacro_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  aic_training_interfaces__srv__ExpandXacro_Request__Sequence__fini(&msg->request);
  // response
  aic_training_interfaces__srv__ExpandXacro_Response__Sequence__fini(&msg->response);
}

bool
aic_training_interfaces__srv__ExpandXacro_Event__are_equal(const aic_training_interfaces__srv__ExpandXacro_Event * lhs, const aic_training_interfaces__srv__ExpandXacro_Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // request
  if (!aic_training_interfaces__srv__ExpandXacro_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!aic_training_interfaces__srv__ExpandXacro_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
aic_training_interfaces__srv__ExpandXacro_Event__copy(
  const aic_training_interfaces__srv__ExpandXacro_Event * input,
  aic_training_interfaces__srv__ExpandXacro_Event * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // request
  if (!aic_training_interfaces__srv__ExpandXacro_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!aic_training_interfaces__srv__ExpandXacro_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

aic_training_interfaces__srv__ExpandXacro_Event *
aic_training_interfaces__srv__ExpandXacro_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Event * msg = (aic_training_interfaces__srv__ExpandXacro_Event *)allocator.allocate(sizeof(aic_training_interfaces__srv__ExpandXacro_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(aic_training_interfaces__srv__ExpandXacro_Event));
  bool success = aic_training_interfaces__srv__ExpandXacro_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
aic_training_interfaces__srv__ExpandXacro_Event__destroy(aic_training_interfaces__srv__ExpandXacro_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    aic_training_interfaces__srv__ExpandXacro_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
aic_training_interfaces__srv__ExpandXacro_Event__Sequence__init(aic_training_interfaces__srv__ExpandXacro_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Event * data = NULL;

  if (size) {
    data = (aic_training_interfaces__srv__ExpandXacro_Event *)allocator.zero_allocate(size, sizeof(aic_training_interfaces__srv__ExpandXacro_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = aic_training_interfaces__srv__ExpandXacro_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        aic_training_interfaces__srv__ExpandXacro_Event__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
aic_training_interfaces__srv__ExpandXacro_Event__Sequence__fini(aic_training_interfaces__srv__ExpandXacro_Event__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      aic_training_interfaces__srv__ExpandXacro_Event__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

aic_training_interfaces__srv__ExpandXacro_Event__Sequence *
aic_training_interfaces__srv__ExpandXacro_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_training_interfaces__srv__ExpandXacro_Event__Sequence * array = (aic_training_interfaces__srv__ExpandXacro_Event__Sequence *)allocator.allocate(sizeof(aic_training_interfaces__srv__ExpandXacro_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = aic_training_interfaces__srv__ExpandXacro_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
aic_training_interfaces__srv__ExpandXacro_Event__Sequence__destroy(aic_training_interfaces__srv__ExpandXacro_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    aic_training_interfaces__srv__ExpandXacro_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
aic_training_interfaces__srv__ExpandXacro_Event__Sequence__are_equal(const aic_training_interfaces__srv__ExpandXacro_Event__Sequence * lhs, const aic_training_interfaces__srv__ExpandXacro_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!aic_training_interfaces__srv__ExpandXacro_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
aic_training_interfaces__srv__ExpandXacro_Event__Sequence__copy(
  const aic_training_interfaces__srv__ExpandXacro_Event__Sequence * input,
  aic_training_interfaces__srv__ExpandXacro_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(aic_training_interfaces__srv__ExpandXacro_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    aic_training_interfaces__srv__ExpandXacro_Event * data =
      (aic_training_interfaces__srv__ExpandXacro_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!aic_training_interfaces__srv__ExpandXacro_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          aic_training_interfaces__srv__ExpandXacro_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!aic_training_interfaces__srv__ExpandXacro_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
