/**
 * app.js — 前端交互脚本 / Front-end interaction script
 * EN: Runs after HTML loads; handles confirm dialogs and flash auto-hide.
 * ZH: 在页面加载后运行；处理确认对话框与提示消息自动消失。
 */

// EN: Wait until DOM is fully loaded / ZH: 等待 DOM 完全加载后再执行
document.addEventListener("DOMContentLoaded", () => {
  // EN: Find all buttons/links with data-confirm attribute / ZH: 查找所有带 data-confirm 的按钮
  document.querySelectorAll("[data-confirm]").forEach((btn) => {
    // EN: On click, show browser confirm dialog / ZH: 点击时显示浏览器确认框
    btn.addEventListener("click", (e) => {
      const msg = btn.getAttribute("data-confirm"); // EN: Read confirm message / ZH: 读取确认文案
      if (msg && !window.confirm(msg)) {
        // EN: User cancelled → stop form submit / ZH: 用户取消 → 阻止表单提交
        e.preventDefault();
      }
    });
  });

  // EN: Select flash message elements / ZH: 选中所有顶部提示条元素
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach((el) => {
    // EN: After 5 seconds, fade out / ZH: 5 秒后开始淡出
    setTimeout(() => {
      el.style.opacity = "0"; // EN: Set transparent / ZH: 设为透明
      el.style.transition = "opacity 0.4s"; // EN: Smooth transition / ZH: 平滑过渡动画
      setTimeout(() => el.remove(), 400); // EN: Remove from DOM after fade / ZH: 淡出后从页面移除
    }, 5000);
  });
});
