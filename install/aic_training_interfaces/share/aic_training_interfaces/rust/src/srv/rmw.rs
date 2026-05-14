#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "aic_training_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__aic_training_interfaces__srv__ExpandXacro_Request() -> *const std::ffi::c_void;
}

#[link(name = "aic_training_interfaces__rosidl_generator_c")]
extern "C" {
    fn aic_training_interfaces__srv__ExpandXacro_Request__init(msg: *mut ExpandXacro_Request) -> bool;
    fn aic_training_interfaces__srv__ExpandXacro_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ExpandXacro_Request>, size: usize) -> bool;
    fn aic_training_interfaces__srv__ExpandXacro_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ExpandXacro_Request>);
    fn aic_training_interfaces__srv__ExpandXacro_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ExpandXacro_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<ExpandXacro_Request>) -> bool;
}

// Corresponds to aic_training_interfaces__srv__ExpandXacro_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ExpandXacro_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub package_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub relative_path: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub xacro_arguments: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,

}



impl Default for ExpandXacro_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !aic_training_interfaces__srv__ExpandXacro_Request__init(&mut msg as *mut _) {
        panic!("Call to aic_training_interfaces__srv__ExpandXacro_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ExpandXacro_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_training_interfaces__srv__ExpandXacro_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_training_interfaces__srv__ExpandXacro_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_training_interfaces__srv__ExpandXacro_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ExpandXacro_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ExpandXacro_Request where Self: Sized {
  const TYPE_NAME: &'static str = "aic_training_interfaces/srv/ExpandXacro_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__aic_training_interfaces__srv__ExpandXacro_Request() }
  }
}


#[link(name = "aic_training_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__aic_training_interfaces__srv__ExpandXacro_Response() -> *const std::ffi::c_void;
}

#[link(name = "aic_training_interfaces__rosidl_generator_c")]
extern "C" {
    fn aic_training_interfaces__srv__ExpandXacro_Response__init(msg: *mut ExpandXacro_Response) -> bool;
    fn aic_training_interfaces__srv__ExpandXacro_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ExpandXacro_Response>, size: usize) -> bool;
    fn aic_training_interfaces__srv__ExpandXacro_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ExpandXacro_Response>);
    fn aic_training_interfaces__srv__ExpandXacro_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ExpandXacro_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<ExpandXacro_Response>) -> bool;
}

// Corresponds to aic_training_interfaces__srv__ExpandXacro_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ExpandXacro_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub xml: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for ExpandXacro_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !aic_training_interfaces__srv__ExpandXacro_Response__init(&mut msg as *mut _) {
        panic!("Call to aic_training_interfaces__srv__ExpandXacro_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ExpandXacro_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_training_interfaces__srv__ExpandXacro_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_training_interfaces__srv__ExpandXacro_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { aic_training_interfaces__srv__ExpandXacro_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ExpandXacro_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ExpandXacro_Response where Self: Sized {
  const TYPE_NAME: &'static str = "aic_training_interfaces/srv/ExpandXacro_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__aic_training_interfaces__srv__ExpandXacro_Response() }
  }
}






#[link(name = "aic_training_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__aic_training_interfaces__srv__ExpandXacro() -> *const std::ffi::c_void;
}

// Corresponds to aic_training_interfaces__srv__ExpandXacro
#[allow(missing_docs, non_camel_case_types)]
pub struct ExpandXacro;

impl rosidl_runtime_rs::Service for ExpandXacro {
    type Request = ExpandXacro_Request;
    type Response = ExpandXacro_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__aic_training_interfaces__srv__ExpandXacro() }
    }
}


