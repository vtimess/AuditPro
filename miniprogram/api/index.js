const { request, uploadFile, downloadFile } = require("../utils/request");

function keywordQuery(keyword) {
  return `?keyword=${encodeURIComponent(String(keyword || "").trim())}`;
}

const authApi = {
  wechatLogin(data) {
    return request({ url: "/auth/wechat-login", method: "POST", data });
  }
};

const homeApi = {
  getHome() { return request({ url: "/home" }); },
  getWorkbench() { return request({ url: "/workbench" }); }
};

const profileApi = {
  get() { return request({ url: "/profile" }); },
  update(data) { return request({ url: "/profile", method: "PATCH", data }); }
};

const attendanceApi = {
  getToday() { return request({ url: "/attendance/today" }); },
  punch(data) { return request({ url: "/attendance/punch", method: "POST", data }); },
  getMonth(month) { return request({ url: `/attendance/month?month=${encodeURIComponent(month)}` }); },
  submitSupplement(data) { return request({ url: "/attendance/supplements", method: "POST", data }); }
};

const policeFilingApi = {
  list(keyword) { return request({ url: `/police-filings${keywordQuery(keyword)}` }); },
  get(id) { return request({ url: `/police-filings/${id}` }); },
  save(id, data) {
    return request({ url: id ? `/police-filings/${id}` : "/police-filings", method: id ? "PUT" : "POST", data });
  },
  remove(id) { return request({ url: `/police-filings/${id}`, method: "DELETE" }); },
  exportExcel() { return downloadFile("/police-filings/export"); }
};

const consumableApi = {
  list(keyword) { return request({ url: `/consumable-purchases${keywordQuery(keyword)}` }); },
  get(id) { return request({ url: `/consumable-purchases/${id}` }); },
  save(id, data) {
    return request({ url: id ? `/consumable-purchases/${id}` : "/consumable-purchases", method: id ? "PUT" : "POST", data });
  },
  remove(id) { return request({ url: `/consumable-purchases/${id}`, method: "DELETE" }); },
  exportExcel(ids) {
    const query = ids && ids.length ? `?ids=${ids.join(",")}` : "";
    return downloadFile(`/consumable-purchases/export${query}`);
  }
};

const safetyApi = {
  list() { return request({ url: "/safety-inspections" }); },
  listRectifications() { return request({ url: "/safety-inspections/rectifications" }); },
  create(data) { return request({ url: "/safety-inspections", method: "POST", data }); },
  rectify(id, data) { return request({ url: `/safety-inspections/hazards/${id}/rectify`, method: "POST", data }); },
  review(id, data) { return request({ url: `/safety-inspections/hazards/${id}/review`, method: "POST", data }); }
};

const fileApi = {
  uploadImage(filePath, businessType, businessId, usageType) {
    return uploadFile({
      url: "/files/upload",
      filePath,
      formData: {
        business_type: businessType,
        business_id: String(businessId),
        usage_type: usageType || "general"
      }
    });
  }
};

const emergencyDrillApi = {
  list(keyword) { return request({ url: `/emergency-drills${keywordQuery(keyword)}` }); },
  importDocument(file) {
    return uploadFile({
      url: "/emergency-drills/import",
      filePath: file.path,
      formData: { original_name: file.name }
    });
  },
  download(path) { return downloadFile(path); }
};

const personnelApi = {
  list(keyword) { return request({ url: `/personnel${keywordQuery(keyword)}` }); },
  get(id) { return request({ url: `/personnel/${id}` }); },
  save(id, data) {
    return request({ url: id ? `/personnel/${id}` : "/personnel", method: id ? "PUT" : "POST", data });
  },
  remove(id) { return request({ url: `/personnel/${id}`, method: "DELETE" }); },
  importExcel(filePath) { return uploadFile({ url: "/personnel/import", filePath }); },
  downloadTemplate() { return downloadFile("/personnel/template"); },
  exportRoster() { return downloadFile("/personnel/export"); }
};

module.exports = {
  authApi,
  homeApi,
  profileApi,
  attendanceApi,
  policeFilingApi,
  consumableApi,
  safetyApi,
  fileApi,
  emergencyDrillApi,
  personnelApi
};
