import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import About from "../views/About.vue";
import Layout from "@/layout/Layout";
const routes = [
  {
    path: "/",
    component: Layout,
    redirect: "/index",
    children: [
      {
        path: "index",
        component: Home,
        name: "Home",
      },
    ],
  },
  {
    path: "/analytics",
    component: Layout,
    redirect: "/analytics",
    redirect: "/analytics/index",
    children: [
      {
        path: "index",
        component: About,
        name: "About",
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
