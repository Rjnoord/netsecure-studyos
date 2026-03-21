import { StyleSheet, Text, View } from "react-native";

import { ScreenShell } from "@/components/ScreenShell";
import { SectionCard } from "@/components/SectionCard";
import { StatCard } from "@/components/StatCard";
import { activeExam, getExamSnapshot } from "@/lib/study-data";
import { theme } from "@/theme";

export default function PredictedScoreScreen() {
  const snapshot = getExamSnapshot(activeExam);
  const prediction = snapshot.prediction;

  return (
    <ScreenShell
      eyebrow="Local Estimate"
      title="Predicted Score"
      description={`A frontend-first view for likely ${activeExam} performance based on saved accuracy, confidence, and question volume.`}
    >
      <View style={styles.statsRow}>
        <StatCard label="Predicted" value={`${prediction.predicted_score}%`} detail="Local estimate only" />
        <StatCard label="Range" value={`${prediction.range_low}-${prediction.range_high}%`} detail="Confidence band" />
      </View>
      <SectionCard title="Confidence Note" subtitle="This text can be connected to the same scoring model used in Streamlit later.">
        <Text style={styles.copy}>{prediction.confidence_note}</Text>
      </SectionCard>
      <SectionCard title="Inputs" subtitle="Planned data sources for the mobile prediction view">
        <Text style={styles.copy}>
          Recent quiz history, weighted domain confidence, total question count, and score consistency. Current synced volume: {prediction.question_volume} questions.
        </Text>
      </SectionCard>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  statsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: theme.spacing.md
  },
  copy: {
    color: theme.colors.text,
    fontSize: theme.type.body,
    lineHeight: 22
  }
});
