const { attendanceApi } = require("../../api/index");

function pad(value) {
  return String(value).padStart(2, "0");
}

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}`;
}

function formatTime(value) {
  if (!value) return "--:--";
  const match = String(value).match(/T(\d{2}:\d{2})/);
  return match ? match[1] : String(value).slice(11, 16);
}

function getLocation() {
  return new Promise((resolve, reject) => {
    wx.getLocation({ type: "gcj02", isHighAccuracy: true, success: resolve, fail: reject });
  });
}

Page({
  data: {
    activeTab: "punch",
    loading: true,
    punching: false,
    locating: false,
    today: null,
    location: null,
    month: currentMonth(),
    monthTitle: "",
    calendar: null,
    calendarCells: [],
    supplementVisible: false,
    selectedDay: null,
    supplementTypes: [],
    supplementTypeIndex: 0,
    supplementTime: "09:00",
    supplementReason: ""
  },

  onLoad() {
    if (!wx.getStorageSync("access_token")) {
      wx.reLaunch({ url: "/pages/login/login" });
      return;
    }
    this.refreshAll();
  },

  onPullDownRefresh() {
    this.refreshAll().finally(() => wx.stopPullDownRefresh());
  },

  switchTab(event) {
    const tab = event.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
    if (tab === "records" && !this.data.calendar) this.loadMonth();
  },

  async refreshAll() {
    this.setData({ loading: true });
    try {
      await Promise.all([this.loadToday(), this.loadMonth()]);
    } finally {
      this.setData({ loading: false });
    }
  },

  async loadToday() {
    try {
      const today = await attendanceApi.getToday();
      if (today.check_in) today.check_in.display_time = formatTime(today.check_in.punched_at);
      if (today.check_out) today.check_out.display_time = formatTime(today.check_out.punched_at);
      this.setData({ today });
    } catch (error) {
      wx.showToast({ title: error.message || "加载打卡状态失败", icon: "none" });
    }
  },

  async locate() {
    this.setData({ locating: true });
    try {
      const result = await getLocation();
      const location = {
        latitude: result.latitude,
        longitude: result.longitude,
        accuracy: result.accuracy || 0,
        location_text: `${Number(result.latitude).toFixed(6)}, ${Number(result.longitude).toFixed(6)}`
      };
      this.setData({ location });
      wx.showToast({ title: "定位成功", icon: "success" });
      return location;
    } catch (error) {
      wx.showModal({
        title: "无法获取位置",
        content: "打卡需要获取当前位置，请在系统设置中允许位置权限。",
        confirmText: "去设置",
        success: (result) => { if (result.confirm) wx.openSetting(); }
      });
      throw error;
    } finally {
      this.setData({ locating: false });
    }
  },

  async punch() {
    if (this.data.punching) return;
    this.setData({ punching: true });
    try {
      const location = this.data.location || await this.locate();
      const result = await attendanceApi.punch(location);
      wx.showToast({ title: result.punch_type === "check_in" ? "上班打卡成功" : "下班打卡成功", icon: "success" });
      await Promise.all([this.loadToday(), this.loadMonth()]);
    } catch (error) {
      if (error && error.message) wx.showToast({ title: error.message, icon: "none" });
    } finally {
      this.setData({ punching: false });
    }
  },

  async loadMonth() {
    try {
      const calendar = await attendanceApi.getMonth(this.data.month);
      const [year, month] = this.data.month.split("-").map(Number);
      const firstWeekday = new Date(year, month - 1, 1).getDay();
      const blanks = Array.from({ length: firstWeekday }, (_, index) => ({ blank: true, key: `blank-${index}` }));
      const days = calendar.days.map((day) => ({ ...day, blank: false, key: day.date }));
      this.setData({
        calendar,
        calendarCells: blanks.concat(days),
        monthTitle: `${year}年${month}月`
      });
    } catch (error) {
      wx.showToast({ title: error.message || "加载考勤月历失败", icon: "none" });
    }
  },

  changeMonth(event) {
    const offset = Number(event.currentTarget.dataset.offset);
    const [year, month] = this.data.month.split("-").map(Number);
    const target = new Date(year, month - 1 + offset, 1);
    this.setData({ month: `${target.getFullYear()}-${pad(target.getMonth() + 1)}` }, () => this.loadMonth());
  },

  selectMonth(event) {
    this.setData({ month: event.detail.value }, () => this.loadMonth());
  },

  selectDay(event) {
    const day = event.currentTarget.dataset.day;
    if (!day || day.blank || day.status === "future") return;
    if (!day.missing_types || !day.missing_types.length) {
      const detail = `上班 ${day.check_in_time || "--:--"}　下班 ${day.check_out_time || "--:--"}`;
      wx.showModal({ title: day.date, content: detail, showCancel: false });
      return;
    }
    if (day.has_pending_supplement) {
      wx.showToast({ title: "已有补卡申请待审核", icon: "none" });
      return;
    }
    const types = day.missing_types.map((value) => ({ value, label: value === "check_in" ? "上班补卡" : "下班补卡" }));
    this.setData({
      supplementVisible: true,
      selectedDay: day,
      supplementTypes: types,
      supplementTypeIndex: 0,
      supplementTime: types[0].value === "check_in" ? "09:00" : "18:00",
      supplementReason: ""
    });
  },

  changeSupplementType(event) {
    const index = Number(event.detail.value);
    const type = this.data.supplementTypes[index];
    this.setData({ supplementTypeIndex: index, supplementTime: type.value === "check_in" ? "09:00" : "18:00" });
  },

  changeSupplementTime(event) { this.setData({ supplementTime: event.detail.value }); },
  inputReason(event) { this.setData({ supplementReason: event.detail.value }); },
  closeSupplement() { this.setData({ supplementVisible: false }); },
  preventClose() {},

  async submitSupplement() {
    const reason = this.data.supplementReason.trim();
    if (reason.length < 2) {
      wx.showToast({ title: "请填写补卡原因", icon: "none" });
      return;
    }
    const type = this.data.supplementTypes[this.data.supplementTypeIndex];
    try {
      await attendanceApi.submitSupplement({
        work_date: this.data.selectedDay.date,
        punch_type: type.value,
        punch_time: `${this.data.supplementTime}:00`,
        reason
      });
      this.setData({ supplementVisible: false });
      wx.showToast({ title: "补卡申请已提交", icon: "success" });
      await this.loadMonth();
    } catch (error) {
      wx.showToast({ title: error.message || "补卡提交失败", icon: "none" });
    }
  }
});
