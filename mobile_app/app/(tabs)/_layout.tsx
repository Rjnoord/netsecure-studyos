import { FontAwesome6, MaterialCommunityIcons } from "@expo/vector-icons";
import { Tabs } from "expo-router";

import { theme } from "@/theme";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.colors.accent,
        tabBarInactiveTintColor: theme.colors.textMuted,
        tabBarStyle: {
          backgroundColor: "#ffffff",
          borderTopColor: theme.colors.border,
          height: 72,
          paddingTop: 8
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: "700"
        }
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: "Dashboard",
          tabBarIcon: ({ color, size }) => <MaterialCommunityIcons name="view-dashboard-outline" color={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="quiz"
        options={{
          title: "Quiz",
          tabBarIcon: ({ color, size }) => <FontAwesome6 name="list-check" color={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="exam-simulator"
        options={{
          title: "Exam",
          tabBarIcon: ({ color, size }) => <MaterialCommunityIcons name="timer-sand" color={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="weak-topics"
        options={{
          title: "Weak",
          tabBarIcon: ({ color, size }) => <MaterialCommunityIcons name="target-account" color={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="study-plan"
        options={{
          title: "Plan",
          tabBarIcon: ({ color, size }) => <MaterialCommunityIcons name="calendar-check-outline" color={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="cheat-sheets"
        options={{
          title: "Cheat",
          tabBarIcon: ({ color, size }) => <MaterialCommunityIcons name="notebook-outline" color={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="predicted-score"
        options={{
          title: "Score",
          tabBarIcon: ({ color, size }) => <MaterialCommunityIcons name="chart-line" color={color} size={size} />
        }}
      />
    </Tabs>
  );
}
