import { Link } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { theme } from "@/theme";

export default function NotFoundScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Screen not found</Text>
      <Link href="/dashboard" style={styles.link}>
        Return to Dashboard
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.colors.background,
    padding: theme.spacing.lg,
    gap: theme.spacing.md
  },
  title: {
    color: theme.colors.text,
    fontSize: 24,
    fontWeight: "700"
  },
  link: {
    color: theme.colors.accent,
    fontSize: 16,
    fontWeight: "700"
  }
});
