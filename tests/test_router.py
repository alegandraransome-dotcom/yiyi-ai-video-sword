from __future__ import annotations

import unittest
from pathlib import Path

from yi_runtime.compiler import RuntimeCompiler
from yi_runtime.router import TaskRouter


ROOT = Path(__file__).resolve().parents[1]


class RouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.router = TaskRouter(RuntimeCompiler.from_source(ROOT).manifest)

    def test_handoff_command_matrix(self) -> None:
        cases = {
            "继续": "continuation",
            "直接正式做33-1": "formal-production",
            "第4镜不行，人物离太近": "local-revision",
            "以一，构图": "directing",
            "看片返工，这个视频又多手了": "review-rework",
            "现在切到资产工作，做同场景反打": "asset-production",
        }
        for task, expected in cases.items():
            with self.subTest(task=task):
                self.assertEqual(self.router.route(task).mode, expected)

    def test_asset_patch_inherits_artifact_type(self) -> None:
        decision = self.router.route(
            "只改一件事：把小推车向画面右侧移动，其他所有东西不变。",
            current_mode="asset-production",
        )
        self.assertEqual(decision.mode, "asset-production")

    def test_negated_formal_output_does_not_hijack_planning(self) -> None:
        preproduction = self.router.route(
            "先做剧本统筹与开拍准备，不要写正式分镜。人物资产暂时没有。"
        )
        self.assertEqual(preproduction.mode, "preproduction")
        directing = self.router.route(
            "先做这个事件后的群体反应设计，不要正式分镜。"
        )
        self.assertEqual(directing.mode, "directing")
        for task in (
            "不做正式分镜，先讨论人物动机。",
            "我不想做正式分镜，先讨论人物动机。",
            "不打算写正式分镜，先讨论人物动机。",
        ):
            with self.subTest(task=task):
                self.assertEqual(self.router.route(task).mode, "preproduction")

    def test_negated_asset_then_positive_formal(self) -> None:
        self.assertEqual(
            self.router.route("不是资产工作，是正式分镜").mode,
            "formal-production",
        )

    def test_explicit_switch_beats_active_asset_patch_heuristic(self) -> None:
        decision = self.router.route(
            "现在切回正式分镜，台词保持不变",
            current_mode="asset-production",
        )
        self.assertEqual(decision.mode, "formal-production")

    def test_later_positive_occurrence_beats_earlier_negation(self) -> None:
        self.assertEqual(
            self.router.route("不要写正式分镜，后来确认还是正式分镜").mode,
            "formal-production",
        )

    def test_double_negation_is_a_positive_instruction(self) -> None:
        for task in (
            "不得不写正式分镜",
            "不能不做正式分镜",
            "不得不开始写正式分镜",
            "不能不进行正式分镜",
            "不是不需要正式分镜",
            "并非不用正式分镜",
            "不能没有正式分镜",
            "不可能不做正式分镜",
            "没有不做正式分镜",
        ):
            with self.subTest(task=task):
                self.assertEqual(self.router.route(task).mode, "formal-production")

    def test_modal_negation_does_not_trigger_formal_output(self) -> None:
        for task in (
            "不能做正式分镜，先讨论人物动机",
            "不得写正式分镜，先讨论",
            "不可能做正式分镜，先讨论",
        ):
            with self.subTest(task=task):
                self.assertEqual(self.router.route(task).mode, "preproduction")

    def test_negated_asset_patch_does_not_override_formal_route(self) -> None:
        for task in ("不要局部修改，重做完整脚本", "不要只改，直接完整脚本"):
            with self.subTest(task=task):
                self.assertEqual(
                    self.router.route(task, current_mode="asset-production").mode,
                    "formal-production",
                )

    def test_bie_de_is_not_a_negation_prefix(self) -> None:
        self.assertEqual(
            self.router.route("别的不说，正式分镜").mode,
            "formal-production",
        )


if __name__ == "__main__":
    unittest.main()
