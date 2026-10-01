const router = require("express").Router();
const { verifyMiddleware, rVerifyMiddleware, studentVerifyMiddleware, verifyResourceIsForUser } = require("../middleware/auth");
const {
  saveLessonAnalysis,
  lessonAddBookmark,
  lessonSwitchBookmark,
  lessonSaveBookmark,
  lessonEdit,
  lessonDelete,
  lessonBookmarkAddAction,
  lessonBookmarkAddQuestion,
  lessonBookmarkEditQuestion,
  lessonBookmarkEditAction,
  lessonDeleteBookmark,
} = require("../controllers/lesson");
const { getLesson, checkLessonBelongsToUser, checkBookmarkBelongsToUser } = require("../controllers/course");
const { recordFeedback, getAllFeedbackForLesson, watchedVideo, exportFeedbackForLesson } = require("../controllers/feedback");
const { logInteraction } = require('../controllers/log')

const ownsLesson = verifyResourceIsForUser(checkLessonBelongsToUser);
const ownsBookmark = verifyResourceIsForUser(checkBookmarkBelongsToUser);

router.get("/:id", getLesson);
router.get("/:id/feedback", verifyMiddleware, ownsLesson, getAllFeedbackForLesson);
router.get("/:id/feedback-export", rVerifyMiddleware, exportFeedbackForLesson);

router.post("/:id", studentVerifyMiddleware, recordFeedback);
router.post("/:id/watched", studentVerifyMiddleware, watchedVideo);
router.post("/:id/log", studentVerifyMiddleware, logInteraction);

router.post("/:id/analysis", verifyMiddleware, ownsLesson, saveLessonAnalysis);

router.put("/bookmark/save/:bookmark_id", verifyMiddleware, ownsBookmark, lessonSaveBookmark);
router.put("/bookmark/:bookmark_id/add-question", verifyMiddleware, ownsBookmark, lessonBookmarkAddQuestion);
router.put("/bookmark/:bookmark_id/edit-questions", verifyMiddleware, ownsBookmark, lessonBookmarkEditQuestion);
router.put("/bookmark/:bookmark_id/add-action", verifyMiddleware, ownsBookmark, lessonBookmarkAddAction);
router.put("/bookmark/:bookmark_id/edit-actions", verifyMiddleware, ownsBookmark, lessonBookmarkEditAction);
router.put("/:id", verifyMiddleware, ownsLesson, lessonEdit);
router.put("/:id/bookmark/add", verifyMiddleware, ownsLesson, lessonAddBookmark);
router.put("/:id/bookmark/switch", verifyMiddleware, ownsLesson, lessonSwitchBookmark);
router.put("/:id/bookmark/delete", verifyMiddleware, ownsLesson, lessonDeleteBookmark);

router.delete("/:id", verifyMiddleware, ownsLesson, lessonDelete);

module.exports = router;
