import { StyleSheet, Text } from "react-native";

import { ScreenShell } from "@/components/ScreenShell";
import { SectionCard } from "@/components/SectionCard";
import { activeExam, getExamSnapshot } from "@/lib/study-data";
import { theme } from "@/theme";

export default function CheatSheetsScreen() {
  const snapshot = getExamSnapshot(activeExam);
  const topic = snapshot.recommended_next_topic.topic;

  return (
    <ScreenShell
      eyebrow="Compressed Review"
      title="Cheat Sheets"
      description={`A mobile-friendly cheat-sheet layout for ${activeExam} key terms, memory hooks, and common mistakes.`}
    >
      <SectionCard title={topic} subtitle="Why it matters">
        <Text style={styles.copy}>{snapshot.recommended_next_topic.reason}</Text>
      </SectionCard>
      <SectionCard title="Key Terms" subtitle="Short-form memory anchors">
        <Text style={styles.copy}>These terms can be filled from the local cheat-sheet store once mobile study content is synced.</Text>
      </SectionCard>
      <SectionCard title="Watch-Outs" subtitle="Common confusion patterns">
        <Text style={styles.copy}>Common mistakes from the Streamlit cheat sheets can be surfaced here after the next content sync step.</Text>
      </SectionCard>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  copy: {
    color: theme.colors.text,
    fontSize: theme.type.body,
    lineHeight: 22
  }
});
