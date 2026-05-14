#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to aic_training_interfaces__srv__ExpandXacro_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ExpandXacro_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub package_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub relative_path: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub xacro_arguments: Vec<std::string::String>,

}



impl Default for ExpandXacro_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ExpandXacro_Request::default())
  }
}

impl rosidl_runtime_rs::Message for ExpandXacro_Request {
  type RmwMsg = super::srv::rmw::ExpandXacro_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        package_name: msg.package_name.as_str().into(),
        relative_path: msg.relative_path.as_str().into(),
        xacro_arguments: msg.xacro_arguments
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        package_name: msg.package_name.as_str().into(),
        relative_path: msg.relative_path.as_str().into(),
        xacro_arguments: msg.xacro_arguments
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      package_name: msg.package_name.to_string(),
      relative_path: msg.relative_path.to_string(),
      xacro_arguments: msg.xacro_arguments
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
    }
  }
}


// Corresponds to aic_training_interfaces__srv__ExpandXacro_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ExpandXacro_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub xml: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for ExpandXacro_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ExpandXacro_Response::default())
  }
}

impl rosidl_runtime_rs::Message for ExpandXacro_Response {
  type RmwMsg = super::srv::rmw::ExpandXacro_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        xml: msg.xml.as_str().into(),
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        xml: msg.xml.as_str().into(),
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      xml: msg.xml.to_string(),
      message: msg.message.to_string(),
    }
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


