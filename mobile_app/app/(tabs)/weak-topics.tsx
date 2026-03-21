import { StyleSheet, Text, View } from "react-native";

import { ScreenShell } from "@/components/ScreenShell";
import { SectionCard } from "@/components/SectionCard";
import { activeExam, getExamSnapshot } from "@/lib/study-data";
import { theme } from "@/theme";

export default function WeakTopicsScreen() {
  const snapshot = getExamSnapshot(activeExam);
  const topWeak = snapshot.weak_topics[0];
  const recovering = snapshot.strong_topics[0];

  return (
    <ScreenShell
      eyebrow="Adaptive Review"
      title="Weak Topics"
      description={`A mobile radar for ${activeExam} recent misses, priority pressure, and topics that are already recovering.`}
    >
      <SectionCard title="Highest Priority" subtitle="This placeholder shows how the future adaptive queue can look on mobile.">
        {topWeak ? (
          <>
            <View style={styles.row}>
              <Text style={styles.topic}>{topWeak.topic}</Text>
              <Text style={styles.badge}>{topWeak.weighted_accuracy}%</Text>
            </View>
            <Text style={styles.copy}>Recent misses are still outweighing older recovery, so this remains the next best review target.</Text>
          </>
        ) : (
          <Text style={styles.copy}>No weak-topic history yet. Save practice attempts in Streamlit to populate this queue.</Text>
        )}
      </SectionCard>
      <SectionCard title="Recovering Topics" subtitle="Repeated correct answers can reduce urgency without hiding the topic entirely.">
        <Text style={styles.copy}>
          {recovering
            ? `${recovering.topic} has a ${recovering.correct_streak}-question correct streak, so it should stay warm without dominating the plan.`
            : "Recovering topics appear once the app has both misses and follow-up correct answers in history."}
        </Text>
      </SectionCard>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  topic: {
    color: theme.colors.text,
    fontSize: 18,
    fontWeight: "700"
  },
  badge: {
    color: theme.colors.warning,
    backgroundColor: theme.colors.warningSoft,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 6,
    borderRadius: theme.radius.pill,
    fontWeight: "700"
  },
  copy: {
    color: theme.colors.text,
    fontSize: theme.type.body,
    lineHeight: 22
  }
});
