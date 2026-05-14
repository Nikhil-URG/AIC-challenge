#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "aic_engine_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__aic_engine_interfaces__srv__ResetJoints_Request() -> *const std::ffi::c_void;
}

#[link(name = "aic_engine_interfaces__rosidl_generator_c")]
extern "C" {
    fn aic_engine_interfaces__srv__ResetJoints_Request__init(msg: *mut ResetJoints_Request) -> bool;
    fn aic_engine_interfaces__srv__ResetJoints_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ResetJoints_Request>, size: usize) -> bool;
    fn aic_engine_interfaces__srv__ResetJoints_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ResetJoints_Request>);
    fn aic_engine_interfaces__srv__ResetJoints_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ResetJoints_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<ResetJoints_Request>) -> bool;
}

// Corresponds to aic_engine_interfaces__srv__ResetJoints_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ResetJoints_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub joint_names: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub initial_positions: rosidl_runtime_rs::Sequence<f64>,

}



impl Default for ResetJoints_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !aic_engine_interfaces__srv__ResetJoints_Request__init(&mut msg as *mut _) {
        panic!("Call to aic_engine_interfaces__srv__ResetJoints_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ResetJoints_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_engine_interfaces__srv__ResetJoints_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_engine_interfaces__srv__ResetJoints_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_engine_interfaces__srv__ResetJoints_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ResetJoints_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ResetJoints_Request where Self: Sized {
  const TYPE_NAME: &'static str = "aic_engine_interfaces/srv/ResetJoints_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__aic_engine_interfaces__srv__ResetJoints_Request() }
  }
}


#[link(name = "aic_engine_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__aic_engine_interfaces__srv__ResetJoints_Response() -> *const std::ffi::c_void;
}

#[link(name = "aic_engine_interfaces__rosidl_generator_c")]
extern "C" {
    fn aic_engine_interfaces__srv__ResetJoints_Response__init(msg: *mut ResetJoints_Response) -> bool;
    fn aic_engine_interfaces__srv__ResetJoints_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ResetJoints_Response>, size: usize) -> bool;
    fn aic_engine_interfaces__srv__ResetJoints_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ResetJoints_Response>);
    fn aic_engine_interfaces__srv__ResetJoints_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ResetJoints_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<ResetJoints_Response>) -> bool;
}

// Corresponds to aic_engine_interfaces__srv__ResetJoints_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ResetJoints_Response {
    /// indicate successful reset
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for ResetJoints_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !aic_engine_interfaces__srv__ResetJoints_Response__init(&mut msg as *mut _) {
        panic!("Call to aic_engine_interfaces__srv__ResetJoints_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ResetJoints_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_engine_interfaces__srv__ResetJoints_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_engine_interfaces__srv__ResetJoints_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_engine_interfaces__srv__ResetJoints_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ResetJoints_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ResetJoints_Response where Self: Sized {
  const TYPE_NAME: &'static str = "aic_engine_interfaces/srv/ResetJoints_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__aic_engine_interfaces__srv__ResetJoints_Response() }
  }
}






#[link(name = "aic_engine_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__aic_engine_interfaces__srv__ResetJoints() -> *const std::ffi::c_void;
}

// Corresponds to aic_engine_interfaces__srv__ResetJoints
#[allow(missing_docs, non_camel_case_types)]
pub struct ResetJoints;

impl rosidl_runtime_rs::Service for ResetJoints {
    type Request = ResetJoints_Request;
    type Response = ResetJoints_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__aic_engine_interfaces__srv__ResetJoints() }
    }
}


