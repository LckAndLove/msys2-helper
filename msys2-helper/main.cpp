// main.cpp
// 最小 Qt6 + OpenCV 示例：摄像头预览 + 选择文件夹保存快照
// 依赖：Qt6Widgets, OpenCV（在 CMake 中链接 Qt6::Widgets 和 OpenCV_LIBS）

#include <QApplication>
#include <QMainWindow>
#include <QLabel>
#include <QPushButton>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QFileDialog>
#include <QTimer>
#include <QMessageBox>
#include <QDateTime>
#include <QDir>
#include <QPixmap>
#include <QImage>

#include <opencv2/opencv.hpp>

class MainWindow : public QMainWindow {
public:
    MainWindow(QWidget *parent = nullptr)
        : QMainWindow(parent), cap(0), saveDir(QDir::homePath())
    {
        QWidget *central = new QWidget(this);
        setCentralWidget(central);

        previewLabel = new QLabel;
        previewLabel->setFixedSize(640, 480);
        previewLabel->setStyleSheet("background-color: black;");
        previewLabel->setAlignment(Qt::AlignCenter);

        QPushButton *btnChoose = new QPushButton("选择保存目录");
        QPushButton *btnSave = new QPushButton("保存快照");
        QPushButton *btnQuit = new QPushButton("退出");

        dirLabel = new QLabel(QString("保存目录: %1").arg(saveDir));
        dirLabel->setWordWrap(true);

        QHBoxLayout *h = new QHBoxLayout;
        h->addWidget(btnChoose);
        h->addWidget(btnSave);
        h->addWidget(btnQuit);

        QVBoxLayout *v = new QVBoxLayout(central);
        v->addWidget(previewLabel);
        v->addWidget(dirLabel);
        v->addLayout(h);

        // 摄像头打开失败提示
        if (!cap.isOpened()) {
            QMessageBox::warning(this, "错误", "无法打开摄像头（index 0）。请检查摄像头或设备路径。");
        }

        // 定时器用于捕获帧
        timer = new QTimer(this);
        connect(timer, &QTimer::timeout, this, &MainWindow::grabFrame);
        timer->start(30); // 大约 33 FPS -> 30ms

        connect(btnChoose, &QPushButton::clicked, this, &MainWindow::chooseDir);
        connect(btnSave, &QPushButton::clicked, this, &MainWindow::saveSnapshot);
        connect(btnQuit, &QPushButton::clicked, qApp, &QApplication::quit);

        setWindowTitle("Qt + OpenCV 摄像头示例");
        resize(680, 620);
    }

    ~MainWindow() {
        timer->stop();
        cap.release();
    }

private:
    void grabFrame() {
        if (!cap.isOpened()) return;

        cv::Mat frame;
        if (!cap.read(frame)) return;

        // 若为空，跳过
        if (frame.empty()) return;

        // BGR -> RGB
        cv::Mat rgb;
        cv::cvtColor(frame, rgb, cv::COLOR_BGR2RGB);

        // 转 QImage（复制数据以避免内存问题）
        QImage img((const uchar*)rgb.data, rgb.cols, rgb.rows, static_cast<int>(rgb.step), QImage::Format_RGB888);
        QImage imgCopy = img.copy();

        // 缩放以适应 QLabel 尺寸（保持比例）
        QPixmap pm = QPixmap::fromImage(imgCopy).scaled(previewLabel->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation);
        previewLabel->setPixmap(pm);

        // 保存最近一帧用于快速保存（不阻塞摄像头读取）
        latestFrame = rgb.clone();
    }

    void chooseDir() {
        QString dir = QFileDialog::getExistingDirectory(this, "选择保存目录", saveDir);
        if (!dir.isEmpty()) {
            saveDir = dir;
            dirLabel->setText(QString("保存目录: %1").arg(saveDir));
        }
    }

    void saveSnapshot() {
        if (latestFrame.empty()) {
            QMessageBox::information(this, "提示", "尚未捕获到帧，无法保存。");
            return;
        }
        // 文件名使用时间戳
        QString filename = QDateTime::currentDateTime().toString("yyyyMMdd_HHmmss_zzz") + ".png";
        QString full = QDir(saveDir).filePath(filename);

        // latestFrame 是 RGB 格式，QImage 可直接保存
        QImage img((const uchar*)latestFrame.data, latestFrame.cols, latestFrame.rows, static_cast<int>(latestFrame.step), QImage::Format_RGB888);
        if (img.save(full)) {
            QMessageBox::information(this, "已保存", QString("已保存快照到：%1").arg(full));
        } else {
            QMessageBox::warning(this, "保存失败", "无法将图像保存到指定路径。");
        }
    }

private:
    QLabel *previewLabel;
    QLabel *dirLabel;
    QTimer *timer;
    cv::VideoCapture cap;
    cv::Mat latestFrame;
    QString saveDir;
};

// 不使用 Q_OBJECT，避免 moc 生成依赖；如果需要信号/槽的元对象特性，请用 CMake AUTOMOC 或单独运行 moc。

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    // Qt6 默认启用高 DPI 缩放，无需手动设置

    MainWindow w;
    w.show();
    return app.exec();
}