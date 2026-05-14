// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from aic_engine_interfaces:srv/ResetJoints.idl
// generated code does not contain a copyright notice
#include "aic_engine_interfaces/srv/detail/reset_joints__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `joint_names`
#include "rosidl_runtime_c/string_functions.h"
// Member `initial_positions`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
aic_engine_interfaces__srv__ResetJoints_Request__init(aic_engine_interfaces__srv__ResetJoints_Request * msg)
{
  if (!msg) {
    return false;
  }
  // joint_names
  if (!rosidl_runtime_c__String__Sequence__init(&msg->joint_names, 0)) {
    aic_engine_interfaces__srv__ResetJoints_Request__fini(msg);
    return false;
  }
  // initial_positions
  if (!rosidl_runtime_c__double__Sequence__init(&msg->initial_positions, 0)) {
    aic_engine_interfaces__srv__ResetJoints_Request__fini(msg);
    return false;
  }
  return true;
}

void
aic_engine_interfaces__srv__ResetJoints_Request__fini(aic_engine_interfaces__srv__ResetJoints_Request * msg)
{
  if (!msg) {
    return;
  }
  // joint_names
  rosidl_runtime_c__String__Sequence__fini(&msg->joint_names);
  // initial_positions
  rosidl_runtime_c__double__Sequence__fini(&msg->initial_positions);
}

bool
aic_engine_interfaces__srv__ResetJoints_Request__are_equal(const aic_engine_interfaces__srv__ResetJoints_Request * lhs, const aic_engine_interfaces__srv__ResetJoints_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // joint_names
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->joint_names), &(rhs->joint_names)))
  {
    return false;
  }
  // initial_positions
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->initial_positions), &(rhs->initial_positions)))
  {
    return false;
  }
  return true;
}

bool
aic_engine_interfaces__srv__ResetJoints_Request__copy(
  const aic_engine_interfaces__srv__ResetJoints_Request * input,
  aic_engine_interfaces__srv__ResetJoints_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // joint_names
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->joint_names), &(output->joint_names)))
  {
    return false;
  }
  // initial_positions
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->initial_positions), &(output->initial_positions)))
  {
    return false;
  }
  return true;
}

aic_engine_interfaces__srv__ResetJoints_Request *
aic_engine_interfaces__srv__ResetJoints_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Request * msg = (aic_engine_interfaces__srv__ResetJoints_Request *)allocator.allocate(sizeof(aic_engine_interfaces__srv__ResetJoints_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(aic_engine_interfaces__srv__ResetJoints_Request));
  bool success = aic_engine_interfaces__srv__ResetJoints_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
aic_engine_interfaces__srv__ResetJoints_Request__destroy(aic_engine_interfaces__srv__ResetJoints_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    aic_engine_interfaces__srv__ResetJoints_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
aic_engine_interfaces__srv__ResetJoints_Request__Sequence__init(aic_engine_interfaces__srv__ResetJoints_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Request * data = NULL;

  if (size) {
    data = (aic_engine_interfaces__srv__ResetJoints_Request *)allocator.zero_allocate(size, sizeof(aic_engine_interfaces__srv__ResetJoints_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = aic_engine_interfaces__srv__ResetJoints_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        aic_engine_interfaces__srv__ResetJoints_Request__fini(&data[i - 1]);
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
aic_engine_interfaces__srv__ResetJoints_Request__Sequence__fini(aic_engine_interfaces__srv__ResetJoints_Request__Sequence * array)
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
      aic_engine_interfaces__srv__ResetJoints_Request__fini(&array->data[i]);
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

aic_engine_interfaces__srv__ResetJoints_Request__Sequence *
aic_engine_interfaces__srv__ResetJoints_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Request__Sequence * array = (aic_engine_interfaces__srv__ResetJoints_Request__Sequence *)allocator.allocate(sizeof(aic_engine_interfaces__srv__ResetJoints_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = aic_engine_interfaces__srv__ResetJoints_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
aic_engine_interfaces__srv__ResetJoints_Request__Sequence__destroy(aic_engine_interfaces__srv__ResetJoints_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    aic_engine_interfaces__srv__ResetJoints_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
aic_engine_interfaces__srv__ResetJoints_Request__Sequence__are_equal(const aic_engine_interfaces__srv__ResetJoints_Request__Sequence * lhs, const aic_engine_interfaces__srv__ResetJoints_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!aic_engine_interfaces__srv__ResetJoints_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
aic_engine_interfaces__srv__ResetJoints_Request__Sequence__copy(
  const aic_engine_interfaces__srv__ResetJoints_Request__Sequence * input,
  aic_engine_interfaces__srv__ResetJoints_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(aic_engine_interfaces__srv__ResetJoints_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    aic_engine_interfaces__srv__ResetJoints_Request * data =
      (aic_engine_interfaces__srv__ResetJoints_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!aic_engine_interfaces__srv__ResetJoints_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          aic_engine_interfaces__srv__ResetJoints_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!aic_engine_interfaces__srv__ResetJoints_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
aic_engine_interfaces__srv__ResetJoints_Response__init(aic_engine_interfaces__srv__ResetJoints_Response * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    aic_engine_interfaces__srv__ResetJoints_Response__fini(msg);
    return false;
  }
  return true;
}

void
aic_engine_interfaces__srv__ResetJoints_Response__fini(aic_engine_interfaces__srv__ResetJoints_Response * msg)
{
  if (!msg) {
    return;
  }
  // success
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
aic_engine_interfaces__srv__ResetJoints_Response__are_equal(const aic_engine_interfaces__srv__ResetJoints_Response * lhs, const aic_engine_interfaces__srv__ResetJoints_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
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
aic_engine_interfaces__srv__ResetJoints_Response__copy(
  const aic_engine_interfaces__srv__ResetJoints_Response * input,
  aic_engine_interfaces__srv__ResetJoints_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

aic_engine_interfaces__srv__ResetJoints_Response *
aic_engine_interfaces__srv__ResetJoints_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Response * msg = (aic_engine_interfaces__srv__ResetJoints_Response *)allocator.allocate(sizeof(aic_engine_interfaces__srv__ResetJoints_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(aic_engine_interfaces__srv__ResetJoints_Response));
  bool success = aic_engine_interfaces__srv__ResetJoints_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
aic_engine_interfaces__srv__ResetJoints_Response__destroy(aic_engine_interfaces__srv__ResetJoints_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    aic_engine_interfaces__srv__ResetJoints_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
aic_engine_interfaces__srv__ResetJoints_Response__Sequence__init(aic_engine_interfaces__srv__ResetJoints_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Response * data = NULL;

  if (size) {
    data = (aic_engine_interfaces__srv__ResetJoints_Response *)allocator.zero_allocate(size, sizeof(aic_engine_interfaces__srv__ResetJoints_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = aic_engine_interfaces__srv__ResetJoints_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        aic_engine_interfaces__srv__ResetJoints_Response__fini(&data[i - 1]);
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
aic_engine_interfaces__srv__ResetJoints_Response__Sequence__fini(aic_engine_interfaces__srv__ResetJoints_Response__Sequence * array)
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
      aic_engine_interfaces__srv__ResetJoints_Response__fini(&array->data[i]);
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

aic_engine_interfaces__srv__ResetJoints_Response__Sequence *
aic_engine_interfaces__srv__ResetJoints_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Response__Sequence * array = (aic_engine_interfaces__srv__ResetJoints_Response__Sequence *)allocator.allocate(sizeof(aic_engine_interfaces__srv__ResetJoints_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = aic_engine_interfaces__srv__ResetJoints_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
aic_engine_interfaces__srv__ResetJoints_Response__Sequence__destroy(aic_engine_interfaces__srv__ResetJoints_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    aic_engine_interfaces__srv__ResetJoints_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
aic_engine_interfaces__srv__ResetJoints_Response__Sequence__are_equal(const aic_engine_interfaces__srv__ResetJoints_Response__Sequence * lhs, const aic_engine_interfaces__srv__ResetJoints_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!aic_engine_interfaces__srv__ResetJoints_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
aic_engine_interfaces__srv__ResetJoints_Response__Sequence__copy(
  const aic_engine_interfaces__srv__ResetJoints_Response__Sequence * input,
  aic_engine_interfaces__srv__ResetJoints_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(aic_engine_interfaces__srv__ResetJoints_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    aic_engine_interfaces__srv__ResetJoints_Response * data =
      (aic_engine_interfaces__srv__ResetJoints_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!aic_engine_interfaces__srv__ResetJoints_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          aic_engine_interfaces__srv__ResetJoints_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!aic_engine_interfaces__srv__ResetJoints_Response__copy(
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
// #include "aic_engine_interfaces/srv/detail/reset_joints__functions.h"

bool
aic_engine_interfaces__srv__ResetJoints_Event__init(aic_engine_interfaces__srv__ResetJoints_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    aic_engine_interfaces__srv__ResetJoints_Event__fini(msg);
    return false;
  }
  // request
  if (!aic_engine_interfaces__srv__ResetJoints_Request__Sequence__init(&msg->request, 0)) {
    aic_engine_interfaces__srv__ResetJoints_Event__fini(msg);
    return false;
  }
  // response
  if (!aic_engine_interfaces__srv__ResetJoints_Response__Sequence__init(&msg->response, 0)) {
    aic_engine_interfaces__srv__ResetJoints_Event__fini(msg);
    return false;
  }
  return true;
}

void
aic_engine_interfaces__srv__ResetJoints_Event__fini(aic_engine_interfaces__srv__ResetJoints_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  aic_engine_interfaces__srv__ResetJoints_Request__Sequence__fini(&msg->request);
  // response
  aic_engine_interfaces__srv__ResetJoints_Response__Sequence__fini(&msg->response);
}

bool
aic_engine_interfaces__srv__ResetJoints_Event__are_equal(const aic_engine_interfaces__srv__ResetJoints_Event * lhs, const aic_engine_interfaces__srv__ResetJoints_Event * rhs)
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
  if (!aic_engine_interfaces__srv__ResetJoints_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!aic_engine_interfaces__srv__ResetJoints_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
aic_engine_interfaces__srv__ResetJoints_Event__copy(
  const aic_engine_interfaces__srv__ResetJoints_Event * input,
  aic_engine_interfaces__srv__ResetJoints_Event * output)
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
  if (!aic_engine_interfaces__srv__ResetJoints_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!aic_engine_interfaces__srv__ResetJoints_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

aic_engine_interfaces__srv__ResetJoints_Event *
aic_engine_interfaces__srv__ResetJoints_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Event * msg = (aic_engine_interfaces__srv__ResetJoints_Event *)allocator.allocate(sizeof(aic_engine_interfaces__srv__ResetJoints_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(aic_engine_interfaces__srv__ResetJoints_Event));
  bool success = aic_engine_interfaces__srv__ResetJoints_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
aic_engine_interfaces__srv__ResetJoints_Event__destroy(aic_engine_interfaces__srv__ResetJoints_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    aic_engine_interfaces__srv__ResetJoints_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
aic_engine_interfaces__srv__ResetJoints_Event__Sequence__init(aic_engine_interfaces__srv__ResetJoints_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Event * data = NULL;

  if (size) {
    data = (aic_engine_interfaces__srv__ResetJoints_Event *)allocator.zero_allocate(size, sizeof(aic_engine_interfaces__srv__ResetJoints_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = aic_engine_interfaces__srv__ResetJoints_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        aic_engine_interfaces__srv__ResetJoints_Event__fini(&data[i - 1]);
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
aic_engine_interfaces__srv__ResetJoints_Event__Sequence__fini(aic_engine_interfaces__srv__ResetJoints_Event__Sequence * array)
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
      aic_engine_interfaces__srv__ResetJoints_Event__fini(&array->data[i]);
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

aic_engine_interfaces__srv__ResetJoints_Event__Sequence *
aic_engine_interfaces__srv__ResetJoints_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  aic_engine_interfaces__srv__ResetJoints_Event__Sequence * array = (aic_engine_interfaces__srv__ResetJoints_Event__Sequence *)allocator.allocate(sizeof(aic_engine_interfaces__srv__ResetJoints_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = aic_engine_interfaces__srv__ResetJoints_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
aic_engine_interfaces__srv__ResetJoints_Event__Sequence__destroy(aic_engine_interfaces__srv__ResetJoints_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    aic_engine_interfaces__srv__ResetJoints_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
aic_engine_interfaces__srv__ResetJoints_Event__Sequence__are_equal(const aic_engine_interfaces__srv__ResetJoints_Event__Sequence * lhs, const aic_engine_interfaces__srv__ResetJoints_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!aic_engine_interfaces__srv__ResetJoints_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
aic_engine_interfaces__srv__ResetJoints_Event__Sequence__copy(
  const aic_engine_interfaces__srv__ResetJoints_Event__Sequence * input,
  aic_engine_interfaces__srv__ResetJoints_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(aic_engine_interfaces__srv__ResetJoints_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    aic_engine_interfaces__srv__ResetJoints_Event * data =
      (aic_engine_interfaces__srv__ResetJoints_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!aic_engine_interfaces__srv__ResetJoints_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          aic_engine_interfaces__srv__ResetJoints_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!aic_engine_interfaces__srv__ResetJoints_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
