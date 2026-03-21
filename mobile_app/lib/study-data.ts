import syncData from "@/data/mobile_sync.json";

type ExamKey = keyof typeof syncData.exams;

export const activeExam: ExamKey = "Security+";

export function getProfile() {
  return syncData.profile;
}

export function getExamSnapshot(exam: ExamKey = activeExam) {
  return syncData.exams[exam];
}

export function getExamOptions(): ExamKey[] {
  return Object.keys(syncData.exams) as ExamKey[];
}
