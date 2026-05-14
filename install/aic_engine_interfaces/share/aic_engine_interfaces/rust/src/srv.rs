#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to aic_engine_interfaces__srv__ResetJoints_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ResetJoints_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub joint_names: Vec<std::string::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub initial_positions: Vec<f64>,

}



impl Default for ResetJoints_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ResetJoints_Request::default())
  }
}

impl rosidl_runtime_rs::Message for ResetJoints_Request {
  type RmwMsg = super::srv::rmw::ResetJoints_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        joint_names: msg.joint_names
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        initial_positions: msg.initial_positions.into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        joint_names: msg.joint_names
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        initial_positions: msg.initial_positions.as_slice().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      joint_names: msg.joint_names
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
      initial_positions: msg.initial_positions
          .into_iter()
          .collect(),
    }
  }
}


// Corresponds to aic_engine_interfaces__srv__ResetJoints_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ResetJoints_Response {
    /// indicate successful reset
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for ResetJoints_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ResetJoints_Response::default())
  }
}

impl rosidl_runtime_rs::Message for ResetJoints_Response {
  type RmwMsg = super::srv::rmw::ResetJoints_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      message: msg.message.to_string(),
    }
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


